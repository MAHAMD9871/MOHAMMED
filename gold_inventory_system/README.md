# نظام الجرد الشهري لمصنع الذهب

تشغيل التطبيق:

1) تثبيت المتطلبات:

```bash
pip install -r requirements.txt
```

2) تشغيل البرنامج:

```bash
python -m gold_inventory_system.main
```

- قاعدة البيانات SQLite تنشأ تلقائياً داخل مجلد `data/`.
- النسخ الاحتياطي يتم تلقائياً داخل `backups/` عند حفظ الجرد والأصناف.
- تقارير HTML/Excel تحفظ داخل `exports/`.