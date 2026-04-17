"""
🚨 PRIORITY ALERT SYSTEM - Interactive BA Dashboard
User-friendly interface for Business Analysts team
Version: 1.2 - OCR Enabled

Run: streamlit run app.py
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="BA Priority Alert System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZE SESSION STATE
# ============================================================================

if 'meetings' not in st.session_state:
    st.session_state.meetings = []
if 'jira_data' not in st.session_state:
    st.session_state.jira_data = {'BI': {}, 'DWH': {}}
if 'calendar_uploaded' not in st.session_state:
    st.session_state.calendar_uploaded = False
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_calendar_text(text):
    """Parse calendar OCR text"""
    meetings = []
    lines = text.strip().split('\n')
    
    current_day = None
    day_number = None
    
    for line in lines:
        # Detect day of week
        day_match = re.match(r'^(Monday|Tuesday|Wednesday|Thursday|Friday)', 
                             line.strip(), re.IGNORECASE)
        if day_match:
            current_day = day_match.group(1)
            continue
            
        # Detect day number
        if re.match(r'^\d{1,2}$', line.strip()):
            day_number = line.strip()
            continue
            
        # Detect meetings
        if any(kw in line for kw in ['Microsoft Teams', 'Meeting', 'Refinement', 'Planning']):
            meeting_name = re.split(r'Microsoft Teams|Meeting', line)[0].strip()
            
            if meeting_name and current_day:
                meeting_type = classify_meeting(meeting_name)
                
                meetings.append({
                    'day': current_day,
                    'day_number': day_number,
                    'name': meeting_name,
                    'type': meeting_type,
                    'requires_tickets': meeting_type in ['BI Backlog Refinement', 
                                                         'DWH - Backlog refinement', 
                                                         'Sprint Planning']
                })
    
    return meetings


def classify_meeting(name):
    """Classify meeting type"""
    name_lower = name.lower()
    
    if 'bi' in name_lower and 'refinement' in name_lower:
        return 'BI Backlog Refinement'
    elif 'dwh' in name_lower and 'refinement' in name_lower:
        return 'DWH - Backlog refinement'
    elif 'sprint' in name_lower and 'planning' in name_lower:
        return 'Sprint Planning'
    elif 'priorit' in name_lower:
        return 'Prioritization'
    else:
        return 'Other'


def calculate_alerts(jira_data):
    """Calculate alert severity"""
    alerts = []
    
    for board in ['BI', 'DWH']:
        if board not in jira_data or not jira_data[board]:
            continue
            
        data = jira_data[board]
        
        # HIGH: Blocked tickets
        if data.get('blocked', 0) > 0:
            alerts.append({
                'severity': 'HIGH',
                'board': board,
                'icon': '🔴',
                'message': f"{data['blocked']} tichet(e) BLOCKED",
                'action': 'Unblock urgent sau escaladează'
            })
        
        # HIGH: Refinement without AC
        missing_ac = data.get('backlog_refinement', 0) - data.get('with_ac', 0)
        if missing_ac > 0:
            alerts.append({
                'severity': 'HIGH',
                'board': board,
                'icon': '🔴',
                'message': f"{missing_ac} tichet(e) fără Acceptance Criteria",
                'action': 'Completează AC până JOI 18:00'
            })
        
        # MEDIUM: Sprint not started
        if data.get('in_sprint_not_started', 0) > 0:
            alerts.append({
                'severity': 'MEDIUM',
                'board': board,
                'icon': '🟡',
                'message': f"{data['in_sprint_not_started']} tichet(e) în sprint dar nu în progress",
                'action': 'Ping devs pentru status update'
            })
    
    return alerts


def generate_report_text(meetings, jira_data, alerts):
    """Generate text report for Teams"""
    current_date = datetime.now()
    critical = [m for m in meetings if m['requires_tickets']]
    
    report = f"""🚨 PRIORITY ALERT - {current_date.strftime('%d %B %Y')}

⚠️  MEETINGURI CRITICE URMĂTOARELE 48H:
"""
    
    if critical:
        for m in critical:
            report += f"  📌 {m['day'].upper()} {m.get('day_number', '')} - {m['name']}\n"
    else:
        report += "  ✅ Nu există meetinguri critice\n"
    
    report += "\n📊 STATUS TICHETE:\n"
    for board in ['BI', 'DWH']:
        if board in jira_data and jira_data[board]:
            data = jira_data[board]
            report += f"  {board}: {data.get('backlog_refinement', 0)} în refinement | "
            report += f"{data.get('with_ac', 0)} cu AC ✅ | "
            report += f"{data.get('blocked', 0)} blocked {'❌' if data.get('blocked', 0) > 0 else '✅'}\n"
    
    if alerts:
        report += "\n🚦 ACȚIUNI NECESARE:\n"
        high = [a for a in alerts if a['severity'] == 'HIGH']
        medium = [a for a in alerts if a['severity'] == 'MEDIUM']
        
        for a in high:
            report += f"  {a['icon']} [{a['board']}] {a['message']} → {a['action']}\n"
        for a in medium:
            report += f"  {a['icon']} [{a['board']}] {a['message']} → {a['action']}\n"
    
    return report


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.title("🚨 BA Priority Alert")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigare",
    ["📊 Dashboard", "📅 Upload Calendar", "🎯 Jira Status", "📝 Creează Tichet", "📤 Export Raport"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Quick Stats")

if st.session_state.meetings:
    critical_count = len([m for m in st.session_state.meetings if m['requires_tickets']])
    st.sidebar.metric("Meetinguri critice", critical_count)

total_alerts = 0
for board in ['BI', 'DWH']:
    if board in st.session_state.jira_data:
        data = st.session_state.jira_data[board]
        total_alerts += data.get('blocked', 0)

if total_alerts > 0:
    st.sidebar.error(f"⚠️ {total_alerts} tichete blocate!")
else:
    st.sidebar.success("✅ Nu există blocaje")

st.sidebar.markdown("---")
st.sidebar.caption(f"Ultima actualizare: {datetime.now().strftime('%H:%M')}")

# ============================================================================
# PAGE 1: DASHBOARD
# ============================================================================

if page == "📊 Dashboard":
    st.title("📊 BA Priority Dashboard")
    st.markdown("### Această săptămână - Priorități și Alerte")
    
    if not st.session_state.calendar_uploaded:
        st.warning("👈 Începe prin a uploada calendarul în secțiunea **Upload Calendar**")
        
        st.markdown("---")
        st.markdown("### 📸 Preview - Cum va arăta dashboard-ul")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Meetinguri săptămâna aceasta", "8", delta="2 critice")
        with col2:
            st.metric("Tichete în Refinement", "8", delta="3 noi")
        with col3:
            st.metric("Tichete blocate", "1", delta="-1", delta_color="inverse")
    
    else:
        st.success("✅ Date încărcate cu succes!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_meetings = len(st.session_state.meetings)
            critical = len([m for m in st.session_state.meetings if m['requires_tickets']])
            st.metric("Total Meetinguri", total_meetings, delta=f"{critical} critice")
        
        with col2:
            bi_ref = st.session_state.jira_data.get('BI', {}).get('backlog_refinement', 0)
            dwh_ref = st.session_state.jira_data.get('DWH', {}).get('backlog_refinement', 0)
            st.metric("Tichete Refinement", bi_ref + dwh_ref)
        
        with col3:
            bi_blocked = st.session_state.jira_data.get('BI', {}).get('blocked', 0)
            dwh_blocked = st.session_state.jira_data.get('DWH', {}).get('blocked', 0)
            total_blocked = bi_blocked + dwh_blocked
            st.metric("Tichete Blocate", total_blocked, 
                     delta_color="inverse" if total_blocked > 0 else "normal")
        
        with col4:
            bi_support = st.session_state.jira_data.get('BI', {}).get('support', 0)
            dwh_support = st.session_state.jira_data.get('DWH', {}).get('support', 0)
            st.metric("Tichete Suport", bi_support + dwh_support)
        
        st.markdown("---")
        
        alerts = calculate_alerts(st.session_state.jira_data)
        
        if alerts:
            st.markdown("### 🚦 Alerte Active")
            
            high_alerts = [a for a in alerts if a['severity'] == 'HIGH']
            medium_alerts = [a for a in alerts if a['severity'] == 'MEDIUM']
            
            if high_alerts:
                st.error("#### 🔴 HIGH PRIORITY")
                for alert in high_alerts:
                    with st.expander(f"[{alert['board']}] {alert['message']}", expanded=True):
                        st.markdown(f"**Acțiune:** {alert['action']}")
            
            if medium_alerts:
                st.warning("#### 🟡 MEDIUM PRIORITY")
                for alert in medium_alerts:
                    with st.expander(f"[{alert['board']}] {alert['message']}"):
                        st.markdown(f"**Acțiune:** {alert['action']}")
        else:
            st.success("### ✅ Nu există alerte active - Totul este sub control!")
        
        st.markdown("---")
        st.markdown("### 📅 Calendar Săptămână Curentă")
        
        critical_meetings = [m for m in st.session_state.meetings if m['requires_tickets']]
        other_meetings = [m for m in st.session_state.meetings if not m['requires_tickets']]
        
        if critical_meetings:
            st.markdown("#### ⚠️ Meetinguri care necesită tichete pregătite:")
            for m in critical_meetings:
                st.markdown(f"- **{m['day']} {m.get('day_number', '')}**: {m['name']} ({m['type']})")
        
        if other_meetings:
            with st.expander("📋 Alte meetinguri (fără tichete necesare)"):
                for m in other_meetings:
                    st.markdown(f"- **{m['day']} {m.get('day_number', '')}**: {m['name']}")
        
        st.markdown("---")
        st.markdown("### 🎯 Status Jira - Detaliat")
        
        tab1, tab2 = st.tabs(["BI Board", "DWH Board"])
        
        with tab1:
            if 'BI' in st.session_state.jira_data and st.session_state.jira_data['BI']:
                data = st.session_state.jira_data['BI']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("În Backlog Refinement", data.get('backlog_refinement', 0))
                    st.metric("Cu AC Complete", data.get('with_ac', 0))
                    st.metric("Tichete Suport", data.get('support', 0))
                
                with col2:
                    st.metric("Blocked", data.get('blocked', 0))
                    st.metric("În Sprint - Nu Started", data.get('in_sprint_not_started', 0))
            else:
                st.info("Nu există date pentru BI. Mergi la **Jira Status** pentru a introduce.")
        
        with tab2:
            if 'DWH' in st.session_state.jira_data and st.session_state.jira_data['DWH']:
                data = st.session_state.jira_data['DWH']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("În Backlog Refinement", data.get('backlog_refinement', 0))
                    st.metric("Cu AC Complete", data.get('with_ac', 0))
                    st.metric("Tichete Suport", data.get('support', 0))
                
                with col2:
                    st.metric("Blocked", data.get('blocked', 0))
                    st.metric("În Sprint - Nu Started", data.get('in_sprint_not_started', 0))
            else:
                st.info("Nu există date pentru DWH. Mergi la **Jira Status** pentru a introduce.")

# ============================================================================
# PAGE 2: UPLOAD CALENDAR - WITH WORKING OCR
# ============================================================================

elif page == "📅 Upload Calendar":
    st.title("📅 Upload Calendar Outlook")
    st.markdown("### Pas 1: Screenshot Calendar Săptămânal")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **Instrucțiuni:**
        1. Deschide Outlook Calendar
        2. Schimbă view la **Week View** (vizualizare săptămână)
        3. Fă screenshot la săptămâna curentă (Luni - Vineri)
        4. Uploadează imaginea mai jos SAU folosește text manual
        """)
    
    with col2:
        st.info("💡 **Tip:** OCR funcționează, dar text manual e mai precis!")
    
    st.markdown("---")
    
    # Option 1: Upload image WITH WORKING OCR
    st.markdown("#### Opțiunea 1: Upload Screenshot (cu OCR automat)")
    uploaded_file = st.file_uploader("Uploadează screenshot calendar (.png, .jpg)", 
                                     type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Calendar uplodat", use_column_width=True)
        
        # Try OCR processing
        try:
            import pytesseract
            from PIL import Image
            import io
            
            with st.spinner("🔄 Procesez imaginea cu OCR..."):
                image = Image.open(uploaded_file)
                ocr_text = pytesseract.image_to_string(image, lang='eng')
            
            if ocr_text.strip():
                st.success("✅ OCR procesare reușită!")
                
                with st.expander("📄 Text extras (verifică și corectează dacă e nevoie)", expanded=True):
                    calendar_text_from_ocr = st.text_area(
                        "Text OCR (editabil):",
                        value=ocr_text,
                        height=200,
                        key="ocr_text_area",
                        help="Poți edita textul dacă OCR-ul a greșit ceva"
                    )
                
                if st.button("✅ Procesează Calendar din OCR", type="primary", key="process_ocr"):
                    meetings = parse_calendar_text(calendar_text_from_ocr)
                    st.session_state.meetings = meetings
                    st.session_state.calendar_uploaded = True
                    
                    st.success(f"✅ Succes! Am identificat {len(meetings)} meetinguri")
                    
                    st.markdown("### 📋 Preview Meetinguri Identificate")
                    for m in meetings:
                        status = "✅ Necesită tichete" if m['requires_tickets'] else "⚪ Info only"
                        st.markdown(f"- **{m['day']} {m.get('day_number', '')}**: {m['name']} - {status}")
                    
                    st.info("👉 Continuă la secțiunea **Jira Status**")
            else:
                st.warning("⚠️ OCR nu a putut extrage text. Folosește Opțiunea 2 (Text manual).")
        
        except ImportError:
            st.error("❌ pytesseract nu este instalat. Folosește Opțiunea 2 (Text manual).")
        except Exception as e:
            st.error(f"❌ Eroare OCR: {str(e)}")
            st.info("💡 Folosește Opțiunea 2 (Text manual) ca alternativă.")
    
    st.markdown("---")
    
    # Option 2: Manual text (ALWAYS AVAILABLE)
    st.markdown("#### Opțiunea 2: Text Manual (Recomandat - mai rapid și mai precis)")
    
    calendar_text = st.text_area(
        "Copiază și paste textul din calendar:",
        height=200,
        placeholder="""Exemplu:
Thursday
16
Data Platform Update Microsoft Teams
DWH - Backlog refinement Microsoft Teams Meeting
Friday
17
BI Backlog Refinement Microsoft Teams Meeting
""",
        help="Copiază direct din Outlook",
        key="manual_calendar_text"
    )
    
    if st.button("✅ Procesează Calendar", type="primary", key="process_manual"):
        if calendar_text.strip():
            meetings = parse_calendar_text(calendar_text)
            st.session_state.meetings = meetings
            st.session_state.calendar_uploaded = True
            
            st.success(f"✅ Succes! Am identificat {len(meetings)} meetinguri")
            
            st.markdown("### 📋 Preview Meetinguri Identificate")
            for m in meetings:
                status = "✅ Necesită tichete" if m['requires_tickets'] else "⚪ Info only"
                st.markdown(f"- **{m['day']} {m.get('day_number', '')}**: {m['name']} - {status}")
            
            st.info("👉 Continuă la secțiunea **Jira Status**")
        else:
            st.error("Te rog să introduci textul din calendar")

# ============================================================================
# PAGE 3: JIRA STATUS
# ============================================================================

elif page == "🎯 Jira Status":
    st.title("🎯 Status Tichete Jira")
    st.markdown("### Introdu manual status-ul tichetelor din Jira")
    
    st.info("💡 **Tip:** Deschide Jira boards în alt tab și numără tichetele din fiecare coloană")
    
    tab1, tab2 = st.tabs(["BI Board", "DWH Board"])
    
    with tab1:
        st.markdown("### 📊 BI Backlog Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            bi_backlog_ref = st.number_input(
                "Tichete în Backlog Refinement (BI)",
                min_value=0,
                value=st.session_state.jira_data.get('BI', {}).get('backlog_refinement', 0),
                help="Câte tichete sunt în coloana 'Backlog Refinement'?"
            )
            
            bi_with_ac = st.number_input(
                "Dintre acestea, câte specs complete?",
                min_value=0,
                max_value=bi_backlog_ref,
                value=st.session_state.jira_data.get('BI', {}).get('with_ac', 0),
                help="Acceptance Criteria completate în format Given/When/Then"
            )
            
            bi_support = st.number_input(
                "Tichete Suport (Task - BI)",
                min_value=0,
                value=st.session_state.jira_data.get('BI', {}).get('support', 0)
            )
        
        with col2:
            bi_blocked = st.number_input(
                "Tichete BLOCKED (BI)",
                min_value=0,
                value=st.session_state.jira_data.get('BI', {}).get('blocked', 0),
                help="Status = 'Blocked' sau labels = 'blocked'"
            )
            
            bi_in_sprint = st.number_input(
                "În Sprint dar nu în Progress (BI)",
                min_value=0,
                value=st.session_state.jira_data.get('BI', {}).get('in_sprint_not_started', 0),
                help="Sprint = Current AND Status = 'Backlog'"
            )
        
        if st.button("💾 Salvează Date BI", key="save_bi"):
            st.session_state.jira_data['BI'] = {
                'backlog_refinement': bi_backlog_ref,
                'with_ac': bi_with_ac,
                'blocked': bi_blocked,
                'in_sprint_not_started': bi_in_sprint,
                'support': bi_support
            }
            st.success("✅ Date BI salvate!")
    
    with tab2:
        st.markdown("### 📊 DWH Backlog Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            dwh_backlog_ref = st.number_input(
                "Tichete în Backlog Refinement (DWH)",
                min_value=0,
                value=st.session_state.jira_data.get('DWH', {}).get('backlog_refinement', 0)
            )
            
            dwh_with_ac = st.number_input(
                "Dintre acestea, câte au AC complete?",
                min_value=0,
                max_value=dwh_backlog_ref,
                value=st.session_state.jira_data.get('DWH', {}).get('with_ac', 0)
            )
            
            dwh_support = st.number_input(
                "Tichete Suport (Task - DWH)",
                min_value=0,
                value=st.session_state.jira_data.get('DWH', {}).get('support', 0)
            )
        
        with col2:
            dwh_blocked = st.number_input(
                "Tichete BLOCKED (DWH)",
                min_value=0,
                value=st.session_state.jira_data.get('DWH', {}).get('blocked', 0)
            )
            
            dwh_in_sprint = st.number_input(
                "În Sprint dar nu în Progress (DWH)",
                min_value=0,
                value=st.session_state.jira_data.get('DWH', {}).get('in_sprint_not_started', 0)
            )
        
        if st.button("💾 Salvează Date DWH", key="save_dwh"):
            st.session_state.jira_data['DWH'] = {
                'backlog_refinement': dwh_backlog_ref,
                'with_ac': dwh_with_ac,
                'blocked': dwh_blocked,
                'in_sprint_not_started': dwh_in_sprint,
                'support': dwh_support
            }
            st.success("✅ Date DWH salvate!")
    
    st.markdown("---")
    
    if st.session_state.jira_data.get('BI') or st.session_state.jira_data.get('DWH'):
        st.success("✅ Date Jira salvate! Mergi la **Dashboard** pentru a vedea alertele.")

# ============================================================================
# PAGE 4: CREATE TICKET (Simplified version)
# ============================================================================

elif page == "📝 Creează Tichet":
    st.title("📝 Jira Ticket Creator")
    st.markdown("### Generator ghidat pentru User Stories")
    
    st.info("💡 Completează formularul și primești un tichet Jira gata de copy-paste!")
    
    ticket_type = st.radio("Tip tichet:", ["Story (Dezvoltare)", "Task (Suport)"])
    board = st.selectbox("Board:", ["BI", "DWH", "Data Platform"])
    
    st.markdown("---")
    
    summary = st.text_input(
        "📋 Summary (Titlu scurt):",
        placeholder="Ex: Dashboard Transportation Cost Variance - Regional View"
    )
    
    st.markdown("### 👤 User Story")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        role = st.text_input("As a (rol):", placeholder="Regional Finance Manager")
    with col2:
        action = st.text_input("I want (acțiune):", placeholder="visualize cost variance")
    with col3:
        benefit = st.text_input("So that (beneficiu):", placeholder="identify overruns early")
    
    st.markdown("### 📊 Business Context")
    problem = st.text_area("Problema:", placeholder="• Lipsă vizibilitate\n• Proces manual lung")
    
    st.markdown("---")
    
    if st.button("🎯 Generează Tichet Jira", type="primary"):
        if not summary:
            st.error("Te rog să completezi Summary-ul")
        elif not role or not action or not benefit:
            st.error("Te rog să completezi User Story (toate cele 3 câmpuri)")
        else:
            ticket_text = f"""
SUMMARY: {summary}

TYPE: {ticket_type}
LABELS: {board}, Backlog refinement

USER STORY:
As a **{role}**,
I want to **{action}**,
So that I can **{benefit}**.

BUSINESS CONTEXT:
{problem if problem else '[Completează problema]'}

ACCEPTANCE CRITERIA:
AC1: [Titlu]
  GIVEN [conditie]
  WHEN [actiune]
  THEN [rezultat]

DATA REQUIREMENTS:
DATA SOURCES: [Sistem/tabel]
GRANULARITATE: [Daily/Monthly]
DATA REFRESH: [Frequency]
"""
            
            st.success("✅ Tichet generat! Copiază textul de mai jos în Jira:")
            st.code(ticket_text, language=None)
            
            st.download_button(
                label="📥 Download ca .txt",
                data=ticket_text,
                file_name=f"jira_ticket_{summary.replace(' ', '_')}.txt",
                mime="text/plain"
            )

# ============================================================================
# PAGE 5: EXPORT REPORT
# ============================================================================

elif page == "📤 Export Raport":
    st.title("📤 Export Raport Săptămânal")
    st.markdown("### Generează și trimite raportul pentru echipă")
    
    if not st.session_state.calendar_uploaded:
        st.warning("⚠️ Te rog să uploadezi mai întâi calendarul și datele Jira")
    else:
        alerts = calculate_alerts(st.session_state.jira_data)
        report_text = generate_report_text(st.session_state.meetings, 
                                           st.session_state.jira_data, 
                                           alerts)
        
        st.markdown("### 📋 Preview Raport")
        st.code(report_text, language=None)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="📥 Download pentru Teams",
                data=report_text,
                file_name=f"priority_alert_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                type="primary"
            )
        
        with col2:
            email_html = f"<pre>{report_text}</pre>"
            st.download_button(
                label="📧 Download pentru Email",
                data=email_html,
                file_name=f"priority_alert_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html"
            )

# ============================================================================
# FOOTER
# ============================================================================

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Info")
st.sidebar.caption("BA Priority Alert System v1.2")
st.sidebar.caption("OCR Support: ✅ Enabled")
st.sidebar.caption("© 2026 Data Platform Team")
