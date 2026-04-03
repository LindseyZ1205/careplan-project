from django.contrib import admin

from .models import CarePlan, Doctor, Order, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "mrn", "created_at")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "npi", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "medication_name", "created_at")


@admin.register(CarePlan)
class CarePlanAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "updated_at")
