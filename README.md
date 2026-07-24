# FooDiX
FooDiX – Smart food recommendation and budget management system, using K‑Means clustering, PyQt6 GUI, and SQLite

<div dir="rtl" align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=yellow)
![PyQt6](https://img.shields.io/badge/PyQt6-6.0%2B-41CD52?style=for-the-badge&logo=qt&logoColor=green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.0%2B-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=orange)
![Status](https://img.shields.io/badge/Status-active-brightgreen?style=for-the-badge)
</div>

>  یک اپلیکیشن دسکتاپ هوشمند برای مدیریت وعده‌های غذایی دانشجویان با در نظر گرفتن بودجه، ارزش غذایی و ترجیحات شخصی است. این سیستم با بهره‌گیری از یادگیری ماشین، پیشنهادات شخصی‌سازی‌شده ارائه می‌دهد و به دانشجویان کمک می‌کند تا تغذیه سالم و مقرون‌به‌صرفه‌ای داشته باشند.

---
<div align="center">

##  معرفی پروژه

</div>

مدیریت تغذیه در دوران دانشجویی چالش‌های خاص خود را دارد: بودجه محدود، کمبود وقت و عدم آگاهی از ارزش غذایی. **FooDiX** با ترکیب هوش مصنوعی و رابط کاربری ساده، این چالش‌ها را حل می‌کند. شما می‌توانید غذاهای مورد علاقه‌تان را ثبت کنید، هزینه‌ها را پیگیری کنید، به غذاها امتیاز دهید و پیشنهادات هوشمندانه‌ای متناسب با بودجه و سلیقه‌تان دریافت کنید.

---
<div align="center">

##  ویژگی‌های کلیدی

</div>

<div dir="rtl" align="center">

 **پیشنهاد هوشمند**  
  با استفاده از الگوریتم خوشه‌بندی K-Means و تحلیل داده‌های مصرف، بهترین گزینه‌های غذایی را بر اساس بودجه، کالری، امتیازات و تنوع غذایی پیشنهاد می‌دهد.

 **مدیریت بودجه روزانه و هفتگی**  
  بودجه خود را تعیین کنید و سیستم به‌صورت خودکار هزینه‌های روزانه را محاسبه کرده و هشدار می‌دهد.

 **مدیریت کامل غذاها**  
  افزودن، ویرایش، حذف و جستجوی غذاها بر اساس نام، مواد اولیه، دسته‌بندی و نوع (گیاهی/گوشتی).

 **سیستم امتیازدهی**  
  به غذاهای مصرف‌شده امتیاز دهید تا پیشنهادات بعدی دقیق‌تر شوند. میانگین امتیاز هر غذا به‌روزرسانی می‌شود.

 **تاریخچه مصرف**  
  ثبت وعده‌های مصرف‌شده به همراه هزینه و کالری، امکان حذف موارد اشتباه.

 **تحلیل و آمار**  
  نمایش آمار کلی، پرمصرف‌ترین غذاها، میانگین هزینه‌ها و نمودار سه‌بعدی خوشه‌بندی غذاها (برای ادمین).

 **پیشنهاد غذای جدید توسط کاربر**  
  کاربران عادی می‌توانند غذاهای جدید پیشنهاد دهند و پس از تأیید ادمین، به لیست اصلی اضافه شوند.

 **حالت ادمین**  
  دسترسی به قابلیت‌های مدیریتی مانند افزودن/ویرایش/حذف غذا، تأیید/رد پیشنهادات و مشاهده آمار پیشرفته.

</div>

---
<div align="center">

##  تکنولوژی‌های استفاده‌شده

| فناوری | بخش |
|--------|------|
| PyQt6 | رابط کاربری |
| SQLite | پایگاه داده |
| scikit-learn (KMeans, StandardScaler) | ماشین لرنینگ |
| NumPy, Matplotlib (3D) | محاسبات و نمودار |
| Python 3.1x+ | زبان برنامه نویسی |
</div>

---
<div align="center">

##  نصب و راه‌اندازی

### پیش‌ نیازها
 Python 3.1x+
```bash
pip install  pyqt6 numpy  scikit-learn matplotlib
```
</div>

<div align="center">

### راه اندازی

</div>
<div dir="rtl">

1. **کلون کردن مخزن**
</div>
<div align="center">

```bash
git clone https://github.com/MortezaMotahar/FooDiX.git
cd FooDiX
pip install -r requirements.txt
python FooDiX.py
```
</div>
