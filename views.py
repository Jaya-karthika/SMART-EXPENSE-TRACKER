import csv
import json
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import ExpenseForm
from .models import Expense
from .utils import predict_category


def get_filtered(request):
    """Return (queryset, active_filter) for the logged-in user only."""
    active = request.GET.get("filter", "all")
    qs = Expense.objects.filter(user=request.user)
    today = timezone.localdate()
    if active == "today":
        qs = qs.filter(date=today)
    elif active == "week":
        start = today - timedelta(days=today.weekday())
        qs = qs.filter(date__gte=start, date__lte=today)
    elif active == "month":
        qs = qs.filter(date__year=today.year, date__month=today.month)
    else:
        active = "all"
    return qs, active


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created. Welcome!")
        return redirect("dashboard")
    return render(request, "signup.html", {"form": form})


@login_required
def dashboard(request):
    qs, active = get_filtered(request)
    total = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    by_cat = qs.values("category").annotate(t=Sum("amount")).order_by("-t")
    by_day = qs.values("date").annotate(t=Sum("amount")).order_by("date")
    context = {
        "active": active,
        "total": total,
        "count": qs.count(),
        "cat_labels": [c["category"] for c in by_cat],
        "cat_values": [float(c["t"]) for c in by_cat],
        "day_labels": [d["date"].strftime("%d %b") for d in by_day],
        "day_values": [float(d["t"]) for d in by_day],
    }
    return render(request, "dashboard.html", context)


@login_required
def expense_list(request):
    qs, active = get_filtered(request)
    total = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0")
    return render(request, "expense_list.html", {"expenses": qs, "active": active, "total": total})


@login_required
def add_expense(request):
    form = ExpenseForm(request.POST or None, initial={"date": timezone.localdate()})
    if request.method == "POST" and form.is_valid():
        exp = form.save(commit=False)
        exp.user = request.user
        if form.cleaned_data["category"] == "Auto":
            exp.category = predict_category(exp.description)
        exp.save()
        messages.success(request, f"Expense added in category: {exp.category}")
        return redirect("expense_list")
    return render(request, "expense_form.html", {"form": form, "title": "Add Expense"})


@login_required
def edit_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    form = ExpenseForm(request.POST or None, instance=exp)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        if form.cleaned_data["category"] == "Auto":
            obj.category = predict_category(obj.description)
        obj.save()
        messages.success(request, "Expense updated.")
        return redirect("expense_list")
    return render(request, "expense_form.html", {"form": form, "title": "Edit Expense"})


@login_required
def delete_expense(request, pk):
    exp = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == "POST":
        exp.delete()
        messages.success(request, "Expense deleted.")
        return redirect("expense_list")
    return render(request, "expense_confirm_delete.html", {"expense": exp})


@login_required
def report_csv(request):
    qs, active = get_filtered(request)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="expenses_{active}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Date", "Description", "Category", "Amount", "Notes"])
    for e in qs:
        writer.writerow([e.date, e.description, e.category, e.amount, e.notes])
    return response


@login_required
def report_pdf(request):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    qs, active = get_filtered(request)
    total = qs.aggregate(t=Sum("amount"))["t"] or Decimal("0")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Expense Report ({active})", styles["Title"]),
        Paragraph(f"User: {request.user.username}", styles["Normal"]),
        Spacer(1, 12),
    ]
    data = [["Date", "Description", "Category", "Amount"]]
    for e in qs:
        data.append([str(e.date), e.description[:40], e.category, f"{e.amount}"])
    data.append(["", "", "Total", f"{total}"])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)
    doc.build(elements)

    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="expenses_{active}.pdf"'
    return response
