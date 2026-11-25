# سجل تعديلات اليوم — Sii-Football / SiiMatchMind

- **تنقية الجلب والـ PDF (`scripts/fetch_data.py`):** استبعاد ملفات PDF التنظيمية/القوانين غير المفيدة للنتائج وكتم تحذيرات `pypdf`.
- **توسيع المصادر (`api/sources.json`):** إضافة بطولات ونتائج رسمية لفئتي `amputee-football` و `cp-football` بجانب `blind-football`.
- **تحسين محلل المباريات (`scripts/parse_leagues.py`):** منع التقاط الأوقات (`AM/PM`) والتواريخ والاختصارات (`vs`, `thu`, `sep`) وتوحيد ترقيم `match_id` لكل فئة.
- **تحسين محلل الترتيب (`scripts/parse_standings.py`):** ضبط قراءة النقاط والإحصائيات بدقة (`played`, `won`, `drawn`, `lost`, `points`).
- **ملخص SiiMatchMind (`api/siimatchmind_summary.json`):** تصدير الملخص الموحد وتحديثه فقط عند تغير البيانات الفعلية.
- **سير عمل GitHub Actions (`.github/workflows/update_api.yml`):** توليد وفحص ملفات JSON الحية على GitHub Pages.
