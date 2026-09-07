import json
import urllib.request
ESP32_URL = "http://192.168.4.1/data"

def get_esp32_data():
    try:
        with urllib.request.urlopen(ESP32_URL, timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))
    except:
        return None
        
"""
PressureGuard — لوحة المتابعة المركزية (نموذج أولي بيانات افتراضية)

للتشغيل:
    pip install streamlit plotly pandas --break-system-packages
    streamlit run pressureguard_dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="PressureGuard — لوحة المتابعة", layout="wide", page_icon="🛏️")

# ----------------------------------------------------------------------------
# التصميم العام: خط عربي، اتجاه RTL، بطاقات احترافية
# ----------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans Arabic', sans-serif !important;
    direction: rtl;
}
.block-container { padding-top: 1.5rem; max-width: 1200px; }

.card {
    background: #FFFFFF;
    border: 1px solid #E3E8E6;
    border-radius: 12px;
    padding: 1.1rem 1.4rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0B4F4A;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 2px solid #0B4F4A;
    padding-bottom: 6px;
}
.section-accent-amber .card-title { color: #A8590B; border-bottom-color: #A8590B; }
.section-accent-red .card-title { color: #8A2E2E; border-bottom-color: #8A2E2E; }
.section-accent-green .card-title { color: #146C43; border-bottom-color: #146C43; }
.section-accent-blue .card-title { color: #0C447C; border-bottom-color: #0C447C; }

.badge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 600;
}
.badge-red { background:#F7EAEA; color:#8A2E2E; }
.badge-amber { background:#FBF0E3; color:#A8590B; }
.badge-green { background:#EAF3E8; color:#146C43; }
.badge-gray { background:#F1EFE8; color:#5F5E5A; }

.metric-box {
    background:#F7FAF9; border-radius:10px; padding:0.8rem 1rem; text-align:center;
    border:1px solid #E3E8E6;
}
.metric-box .val { font-size:1.4rem; font-weight:700; color:#0B4F4A; }
.metric-box .lbl { font-size:0.78rem; color:#5F5E5A; margin-top:2px; }

.pressure-cell {
    border-radius:8px; padding:0.9rem 0.4rem; text-align:center; font-size:0.82rem;
    font-weight:600; color:#fff;
}
.disclaimer {
    background:#FBF0E3; border-right:4px solid #A8590B; border-radius:8px;
    padding:0.8rem 1rem; font-size:0.85rem; color:#6b4a1c; margin-top:1.5rem;
}
hr { margin: 0.4rem 0 1rem 0; border-color:#E3E8E6; }
</style>
""", unsafe_allow_html=True)

def card_start(title, icon="", accent=""):
    cls = f"card {accent}" if accent else "card"
    st.markdown(f'<div class="{cls}"><div class="card-title">{icon} {title}</div>', unsafe_allow_html=True)

def card_end():
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# بيانات افتراضية (Mock Data)
# ----------------------------------------------------------------------------
PATIENTS = {
    "سرير 14 — مريض #014": {
        "braden": 13, "الوزن": "78 كجم", "الحالة": "تحذير", "لون_الحالة": "badge-red",
        "الفاصل_العام": 120, "الفاصل_الموصى": 90, "الموعد_القادم": "04:20 م",
        "الدقائق_المتبقية": 38,
        "منطقة_حرجة": "العجز", "اتجاه": "↗ يتجه للتفاقم", "دقائق_للتنبيه": 12,
        "ثقة_التنبؤ": "متوسطة",
        "صمام": "X23", "إجراء_وقت": "03:32 م",
        "قياس_حالة": "مكتملة", "قياس_مدة": "5 دقائق",
        "قياس_قبل": 92, "قياس_بعد": 29,
        "قياس_نجح": True,
        "مدة_الحلقة": 34, "تكرار": 3, "خلال_مدة": "6 ساعات", "تراكم_24س": "1 س 48 د",
        "نسبة_فوق_الأساس": 78,
        "زمن_آخر_تقليب": "1 س 10 د",
        "تفسير": "تراكم ضغط مستمر ومتكرر بمنطقة العجز، مع تأخر بتغيير الوضعية عن المعتاد لهذا المريض",
        "تدخل_مصدر": "ممرض (يدوي)", "تدخل_وقت": "قبل ساعتين وربع",
        "تدخل_نتيجة": "لم يتغير الضغط بشكل كافٍ", "انتقال_حمل": "لا",
        "تصعيد": True,
        "heatmap": {
            "الكتف الأيمن": 22, "أعلى الظهر": 30, "الكتف الأيسر": 25,
            "الظهر الأيمن": 35, "منتصف الظهر": 28, "الظهر الأيسر": 33,
            "الورك الأيمن": 55, "العجز": 92, "الورك الأيسر": 48,
        },
        "history": [
            {"الوقت": "09:10 ص", "المنطقة": "العجز", "المدة": "22 دقيقة", "المصدر": "مفرش (تلقائي)", "النتيجة": "✅ نجح — انخفض الضغط"},
            {"الوقت": "11:40 ص", "المنطقة": "العجز", "المدة": "18 دقيقة", "المصدر": "ممرض", "النتيجة": "🟡 نجح جزئيًا"},
            {"الوقت": "01:55 م", "المنطقة": "العجز", "المدة": "28 دقيقة", "المصدر": "ممرض", "النتيجة": "❌ لم ينجح"},
            {"الوقت": "03:20 م", "المنطقة": "العجز", "المدة": "جارية (34 دقيقة)", "المصدر": "—", "النتيجة": "⏳ بانتظار التدخل"},
        ],
    },
    "سرير 09 — مريض #009": {
        "braden": 16, "الوزن": "65 كجم", "الحالة": "مراقبة", "لون_الحالة": "badge-amber",
        "الفاصل_العام": 120, "الفاصل_الموصى": 110, "الموعد_القادم": "05:05 م", "الدقائق_المتبقية": 63,
        "منطقة_حرجة": "الكعب الأيمن", "اتجاه": "↗ يتجه للتفاقم", "دقائق_للتنبيه": 40,
        "ثقة_التنبؤ": "منخفضة",
        "صمام": "X09", "إجراء_وقت": "قيد الانتظار",
        "قياس_حالة": "جارية", "قياس_مدة": "5 دقائق",
        "قياس_قبل": 65, "قياس_بعد": None,
        "قياس_نجح": None,
        "مدة_الحلقة": 9, "تكرار": 1, "خلال_مدة": "6 ساعات", "تراكم_24س": "22 دقيقة",
        "نسبة_فوق_الأساس": 31,
        "زمن_آخر_تقليب": "35 دقيقة",
        "تفسير": "بداية اتجاه تصاعدي بسيط بمنطقة الكعب، بدون تكرار سابق يُذكر",
        "تدخل_مصدر": "—", "تدخل_وقت": "—", "تدخل_نتيجة": "لا يوجد تدخل سابق اليوم",
        "انتقال_حمل": "—", "تصعيد": False,
        "heatmap": {
            "الكتف الأيمن": 20, "أعلى الظهر": 24, "الكتف الأيسر": 21,
            "الظهر الأيمن": 26, "منتصف الظهر": 23, "الظهر الأيسر": 25,
            "الورك الأيمن": 30, "العجز": 34, "الورك الأيسر": 29,
        },
        "history": [
            {"الوقت": "10:00 ص", "المنطقة": "الكعب الأيمن", "المدة": "9 دقيقة", "المصدر": "—", "النتيجة": "⏳ جارية"},
        ],
    },
    "سرير 22 — مريض #022": {
        "braden": 19, "الوزن": "71 كجم", "الحالة": "مستقر", "لون_الحالة": "badge-green",
        "الفاصل_العام": 120, "الفاصل_الموصى": 120, "الموعد_القادم": "06:00 م", "الدقائق_المتبقية": 95,
        "منطقة_حرجة": "لا يوجد", "اتجاه": "→ مستقر", "دقائق_للتنبيه": None,
        "ثقة_التنبؤ": "—",
        "صمام": None, "إجراء_وقت": None,
        "قياس_حالة": None, "قياس_مدة": None,
        "قياس_قبل": None, "قياس_بعد": None,
        "قياس_نجح": None,
        "مدة_الحلقة": 0, "تكرار": 0, "خلال_مدة": "6 ساعات", "تراكم_24س": "0 دقيقة",
        "نسبة_فوق_الأساس": 8,
        "زمن_آخر_تقليب": "20 دقيقة",
        "تفسير": "جميع المناطق ضمن الحدود الطبيعية مقارنة بخط الأساس الخاص بالمريض",
        "تدخل_مصدر": "—", "تدخل_وقت": "—", "تدخل_نتيجة": "لا حاجة لتدخل", "انتقال_حمل": "—",
        "تصعيد": False,
        "heatmap": {
            "الكتف الأيمن": 15, "أعلى الظهر": 18, "الكتف الأيسر": 16,
            "الظهر الأيمن": 19, "منتصف الظهر": 17, "الظهر الأيسر": 18,
            "الورك الأيمن": 20, "العجز": 22, "الورك الأيسر": 19,
        },
        "history": [
            {"الوقت": "02:00 م", "المنطقة": "—", "المدة": "—", "المصدر": "مفرش (روتيني)", "النتيجة": "✅ لا ملاحظات"},
        ],
    },
}

def pressure_color(v):
    if v >= 70: return "#B23A3A"
    if v >= 40: return "#C97A2B"
    return "#3D8C5B"

# ----------------------------------------------------------------------------
# رأس الصفحة + اختيار السرير
# ----------------------------------------------------------------------------
st.markdown("## 🛏️ PressureGuard — لوحة المتابعة المركزية")
st.caption("عرض تجريبي ببيانات افتراضية لأغراض التوضيح فقط")

col_sel, col_summary = st.columns([2, 3])
with col_sel:
    selected = st.selectbox("اختر السرير / المريض", list(PATIENTS.keys()))

p = PATIENTS[selected]

with col_summary:
    st.markdown(
        f'<div style="display:flex;gap:10px;align-items:center;height:100%;padding-top:22px;">'
        f'<span class="badge {p["لون_الحالة"]}">{p["الحالة"]}</span>'
        f'<span style="color:#5F5E5A;font-size:0.85rem;">آخر تحديث: الآن</span>'
        f'</div>', unsafe_allow_html=True
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# 1. المؤشرات الأساسية
# ----------------------------------------------------------------------------
card_start("المؤشرات الأساسية", "📋")
c1, c2, c3, c4, c5 = st.columns(5)
for col, val, lbl in [
    (c1, p["braden"], "درجة Braden"),
    (c2, p["الوزن"], "الوزن"),
    (c3, p["الحالة"], "الحالة العامة"),
    (c4, p["منطقة_حرجة"], "المنطقة الأكثر تأثرًا"),
    (c5, p["زمن_آخر_تقليب"], "الزمن منذ آخر تقليب"),
]:
    col.markdown(f'<div class="metric-box"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)
card_end()

# ----------------------------------------------------------------------------
# 2. الفاصل الزمني الشخصي للتقليب
# ----------------------------------------------------------------------------
card_start("الفاصل الزمني الشخصي للتقليب", "🕑", "section-accent-blue")
c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="metric-box"><div class="val">كل {p["الفاصل_العام"]} د</div><div class="lbl">المعيار العام</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-box"><div class="val">كل {p["الفاصل_الموصى"]} د</div><div class="lbl">الموصى به لهذا المريض</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-box"><div class="val">{p["الموعد_القادم"]}</div><div class="lbl">موعد التقليب القادم (خلال {p["الدقائق_المتبقية"]} د)</div></div>', unsafe_allow_html=True)
st.caption("مبني على نمط تراكم الضغط الفعلي المتعلَّم من تاريخ هذا المريض، لا على معيار موحد لجميع المرضى.")
card_end()

# ----------------------------------------------------------------------------
# 3. لوحة التنبؤ المبكر + الإجراء الافتراضي التلقائي (مدمجة)
# ----------------------------------------------------------------------------
card_start("التنبؤ المبكر والإجراء الافتراضي التلقائي", "⚡", "section-accent-amber")
if p["دقائق_للتنبيه"] is not None:
    st.markdown("**🔮 التوقع**")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metric-box"><div class="val">{p["اتجاه"]}</div><div class="lbl">اتجاه المنطقة الحرجة</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metric-box"><div class="val">~{p["دقائق_للتنبيه"]} دقيقة</div><div class="lbl">الوقت المتوقع لبلوغ حالة تنبيه</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metric-box"><div class="val">{p["ثقة_التنبؤ"]}</div><div class="lbl">درجة ثقة التنبؤ</div></div>', unsafe_allow_html=True)
    st.caption("مبني على تحليل الضغط عبر الزمن + درجة Braden، مقارنة بنقطة العجز الفردية لهذا المريض — لا عتبة موحدة.")

    st.markdown("---")
    st.markdown(f"**⚙️ الإجراء الافتراضي التلقائي:** فتح صمام الخلية `{p['صمام']}`")
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown('<div class="metric-box"><div class="val">1️⃣</div><div class="lbl">فتح الصمام</div></div>', unsafe_allow_html=True)
    s2.markdown('<div class="metric-box"><div class="val">2️⃣</div><div class="lbl">انتفاش طبيعي للمنطقة</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="metric-box"><div class="val">3️⃣</div><div class="lbl">قياس لمدة {p["قياس_مدة"]}</div></div>', unsafe_allow_html=True)
    s4.markdown('<div class="metric-box"><div class="val">4️⃣</div><div class="lbl">مقارنة قبل/بعد</div></div>', unsafe_allow_html=True)
    st.caption(f"بدأ التنفيذ التلقائي الساعة {p['إجراء_وقت']} — بدون انتظار تدخل بشري.")

    st.markdown("---")
    if p["قياس_حالة"] == "جارية":
        st.info(f"⏳ **فترة القياس جارية الآن** — القراءة قبل الفتح: {p['قياس_قبل']}%. النتيجة تظهر بعد انتهاء مدة القياس ({p['قياس_مدة']}).")
    elif p["قياس_حالة"] == "مكتملة":
        drop_pct = round((p["قياس_قبل"] - p["قياس_بعد"]) / p["قياس_قبل"] * 100)
        m1, m2, m3 = st.columns(3)
        m1.markdown(f'<div class="metric-box"><div class="val">{p["قياس_قبل"]}%</div><div class="lbl">الضغط قبل الفتح</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="metric-box"><div class="val">{p["قياس_بعد"]}%</div><div class="lbl">الضغط بعد {p["قياس_مدة"]}</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="metric-box"><div class="val">-{drop_pct}%</div><div class="lbl">نسبة الانخفاض</div></div>', unsafe_allow_html=True)
        if p["قياس_نجح"]:
            st.success("✅ **النتيجة:** انخفض الضغط بشكل كافٍ — الإجراء التلقائي كافٍ، لا حاجة لتصعيد فوري.")
        else:
            st.error("🔺 **النتيجة:** لم يتغيّر الضغط بشكل كافٍ بعد فتح الصمام — تم تصعيد الحالة لمراجعة الممرض.")
else:
    st.success("لا توجد مناطق تُظهر اتجاهًا تصاعديًا مقلقًا حاليًا، ولا حاجة لأي إجراء تلقائي.")
card_end()

# ----------------------------------------------------------------------------
# 4. خريطة توزيع الضغط الحالي
# ----------------------------------------------------------------------------
card_start("خريطة توزيع الضغط الحالي (نسبة إلى خط الأساس الفردي)", "🗺️")
zones = list(p["heatmap"].items())
cols = st.columns(3)
for i, (zone, val) in enumerate(zones):
    with cols[i % 3]:
        st.markdown(
            f'<div class="pressure-cell" style="background:{pressure_color(val)};">'
            f'{zone}<br><span style="font-size:1.1rem;">{val}%</span></div>',
            unsafe_allow_html=True
        )
        st.write("")
st.caption("النسب معروضة مقارنة بخط الأساس الفردي لكل منطقة عند هذا المريض تحديدًا، لا كقيمة مطلقة موحدة.")
card_end()

# ----------------------------------------------------------------------------
# 5. نمط التكرار
# ----------------------------------------------------------------------------
card_start("نمط التكرار", "📊", "section-accent-red")
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="metric-box"><div class="val">{p["مدة_الحلقة"]} د</div><div class="lbl">مدة الحلقة الحالية</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-box"><div class="val">{p["تكرار"]} مرات</div><div class="lbl">التكرار خلال {p["خلال_مدة"]}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="metric-box"><div class="val">{p["تراكم_24س"]}</div><div class="lbl">إجمالي التعرض (24 ساعة)</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="metric-box"><div class="val">+{p["نسبة_فوق_الأساس"]}%</div><div class="lbl">فوق خط الأساس الفردي</div></div>', unsafe_allow_html=True)
card_end()

# ----------------------------------------------------------------------------
# 6. الرسم الزمني
# ----------------------------------------------------------------------------
card_start("الاتجاه الزمني — المنطقة الأكثر تأثرًا", "📈")
now = datetime.now()
hist_times = [now - timedelta(minutes=m) for m in range(360, -1, -20)]
base = max(p["نسبة_فوق_الأساس"] - 60, 5)
hist_vals = [base + (i * (p["نسبة_فوق_الأساس"] - base) / len(hist_times)) for i in range(len(hist_times))]
future_times = [now + timedelta(minutes=m) for m in range(0, 41, 10)]
future_vals = [p["نسبة_فوق_الأساس"] + i * 6 for i in range(len(future_times))]

fig = go.Figure()
fig.add_trace(go.Scatter(x=hist_times, y=hist_vals, mode="lines", name="القراءات الفعلية",
                          line=dict(color="#0B4F4A", width=3)))
fig.add_trace(go.Scatter(x=future_times, y=future_vals, mode="lines", name="الاتجاه المتوقع",
                          line=dict(color="#C97A2B", width=2, dash="dash")))
fig.add_hline(y=70, line_dash="dot", line_color="#B23A3A", annotation_text="عتبة التنبيه الفردية")
fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10),
                   legend=dict(orientation="h", yanchor="bottom", y=1.02),
                   xaxis_title=None, yaxis_title="% فوق خط الأساس")
st.plotly_chart(fig, use_container_width=True)
card_end()

# ----------------------------------------------------------------------------
# 7. لوحة تفسير الذكاء الاصطناعي
# ----------------------------------------------------------------------------
card_start("تفسير الذكاء الاصطناعي", "🧠")
st.markdown(f'**الخلاصة:** {p["تفسير"]}')
card_end()

# ----------------------------------------------------------------------------
# 8. نتيجة التدخل
# ----------------------------------------------------------------------------
card_start("نتيجة آخر تدخل", "✅" if not p.get("تصعيد") else "🔺",
           "section-accent-green" if not p.get("تصعيد") else "section-accent-red")
c1, c2 = st.columns(2)
c1.markdown(f'<div class="metric-box"><div class="val">{p["تدخل_مصدر"]}</div><div class="lbl">مصدر التدخل</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="metric-box"><div class="val">{p["تدخل_وقت"]}</div><div class="lbl">التوقيت</div></div>', unsafe_allow_html=True)
st.write("")
st.markdown(f"**النتيجة:** {p['تدخل_نتيجة']}  \n**هل انتقل الحمل لمنطقة أخرى؟** {p['انتقال_حمل']}")
if p.get("تصعيد"):
    st.error("🔺 تم تصعيد الأولوية — التدخل السابق لم ينجح في تخفيف الضغط بشكل كافٍ.")
card_end()

# ----------------------------------------------------------------------------
# 9. قائمة أولويات جميع المرضى
# ----------------------------------------------------------------------------
card_start("قائمة أولويات المرضى", "📋")
priority_rows = []
for name, d in PATIENTS.items():
    if d["الحالة"] == "تحذير":
        pr, reason = "🔴 عالية", "تكرار + تدخل سابق فاشل" if d.get("تصعيد") else "نمط ضغط مستمر"
    elif d["الحالة"] == "مراقبة":
        pr, reason = "🟡 متوسطة", "اتجاه تصاعدي مبكر"
    else:
        pr, reason = "🟢 منخفضة", "مستقر"
    priority_rows.append({"السرير": name, "المنطقة": d["منطقة_حرجة"], "الأولوية": pr, "السبب": reason})
st.dataframe(pd.DataFrame(priority_rows), use_container_width=True, hide_index=True)
card_end()

# ----------------------------------------------------------------------------
# 10. السجل التاريخي الكامل
# ----------------------------------------------------------------------------
card_start("السجل التاريخي الكامل", "🗂️")
st.dataframe(pd.DataFrame(p["history"]), use_container_width=True, hide_index=True)
card_end()

# ----------------------------------------------------------------------------
# التنويه الثابت
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="disclaimer">⚠️ مخرجات الذكاء الاصطناعي استشارية وداعمة للقرار، '
    'ولا تُعد تشخيصًا طبيًا ولا تستبدل الحكم السريري للطاقم الصحي.</div>',
    unsafe_allow_html=True
)
