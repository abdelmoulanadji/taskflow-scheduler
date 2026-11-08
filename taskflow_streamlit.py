import itertools
import pandas as pd
import streamlit as st

st.set_page_config(page_title="TaskFlow Scheduler", page_icon="📊", layout="wide")

class Task:
    def __init__(self, name, execution_time, due_date):
        self.name = name
        self.exec_time = float(execution_time)
        self.due_date = float(due_date)

def calculate_schedule_metrics(order):
    clock, total = 0.0, 0.0
    rows = []
    for task in order:
        start = clock
        finish = start + task.exec_time
        delay = max(0.0, finish - task.due_date)
        rows.append({
            "Task": task.name, "Start": start, "Finish": finish,
            "Due date": task.due_date, "Tardiness": delay
        })
        clock = finish
        total += delay
    return rows, total

def spt_method(tasks):
    return calculate_schedule_metrics(sorted(tasks, key=lambda t: t.exec_time))

def edd_method(tasks):
    return calculate_schedule_metrics(sorted(tasks, key=lambda t: t.due_date))

def exact_method(tasks):
    best_rows, best_total = [], float("inf")
    for order in itertools.permutations(tasks):
        rows, total = calculate_schedule_metrics(order)
        if total < best_total:
            best_rows, best_total = rows, total
    return best_rows, best_total

st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#07111f,#12233b);color:#eef4ff}
[data-testid="stSidebar"] {background:#0b1728}
.hero {padding:28px;border-radius:20px;background:linear-gradient(110deg,#15365f,#1d5284);margin-bottom:22px}
.kicker {color:#9bcfff;font-weight:800;letter-spacing:2px;font-size:12px}
.hero h1 {color:white;margin:8px 0;font-size:38px}
.hero p {color:#d5e5f8;margin:0}
div[data-testid="stMetric"] {background:#111f33;border:1px solid #2a4261;padding:14px;border-radius:15px}
</style>
<div class="hero">
<div class="kicker">TASKFLOW · SCHEDULING STUDIO</div>
<h1>Smart Task Scheduler</h1>
<p>Compare SPT, EDD and Exact algorithms to minimize total tardiness.</p>
</div>
""", unsafe_allow_html=True)

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"name":"P1","execution":3.0,"due":5.0},
        {"name":"P2","execution":1.0,"due":2.0},
        {"name":"P3","execution":4.0,"due":7.0},
        {"name":"P4","execution":2.0,"due":4.0},
    ]
if "results" not in st.session_state:
    st.session_state.results = None

def task_objects():
    return [Task(x["name"], x["execution"], x["due"]) for x in st.session_state.tasks]

with st.sidebar:
    st.header("➕ Add a task")
    with st.form("add_task", clear_on_submit=True):
        name = st.text_input("Task name", placeholder="Example: P5")
        execution = st.number_input("Execution time", min_value=0.01, value=1.0, step=0.5)
        due = st.number_input("Due date", min_value=0.0, value=5.0, step=0.5)
        add = st.form_submit_button("Add task", use_container_width=True)
    if add:
        clean = name.strip()
        if not clean:
            st.error("Enter a task name.")
        elif any(x["name"].casefold() == clean.casefold() for x in st.session_state.tasks):
            st.error("Task names must be unique.")
        else:
            st.session_state.tasks.append({"name":clean,"execution":float(execution),"due":float(due)})
            st.session_state.results = None
            st.rerun()

    st.divider()
    st.header("🗑️ Manage tasks")
    if st.session_state.tasks:
        names = [x["name"] for x in st.session_state.tasks]
        chosen = st.selectbox("Choose task", names)
        if st.button("Delete selected task", use_container_width=True):
            st.session_state.tasks = [x for x in st.session_state.tasks if x["name"] != chosen]
            st.session_state.results = None
            st.rerun()
    if st.button("Restore sample tasks", use_container_width=True):
        st.session_state.tasks = [
            {"name":"P1","execution":3.0,"due":5.0},
            {"name":"P2","execution":1.0,"due":2.0},
            {"name":"P3","execution":4.0,"due":7.0},
            {"name":"P4","execution":2.0,"due":4.0},
        ]
        st.session_state.results = None
        st.rerun()

tasks = task_objects()
a, b, c = st.columns(3)
a.metric("Total tasks", len(tasks))
b.metric("Total execution time", f"{sum(t.exec_time for t in tasks):g}")
c.metric("Exact method limit", "9 tasks")

st.subheader("📋 Current tasks")
if st.session_state.tasks:
    st.dataframe(pd.DataFrame(st.session_state.tasks).rename(columns={
        "name":"Task", "execution":"Execution time", "due":"Due date"
    }), use_container_width=True, hide_index=True)
else:
    st.info("No tasks yet. Add one from the sidebar.")

st.subheader("⚙️ Algorithm comparison")
if len(tasks) > 9:
    st.warning("Exact search checks n! possible orders. Reduce the list to 9 tasks or fewer.")
run = st.button("▶ Run all algorithms", type="primary", use_container_width=True,
                disabled=(len(tasks) == 0 or len(tasks) > 9))
if run:
    st.session_state.results = {
        "SPT": spt_method(tasks),
        "EDD": edd_method(tasks),
        "Exact": exact_method(tasks),
    }

if st.session_state.results:
    results = st.session_state.results
    best = min(results, key=lambda k: results[k][1])
    st.success(f"🏆 Best result: {best} · Lowest total tardiness: {results[best][1]:.2f}")

    cols = st.columns(3)
    subtitles = {
        "SPT":"Shortest Processing Time",
        "EDD":"Earliest Due Date",
        "Exact":"Optimal exhaustive search"
    }
    for col, key in zip(cols, ["SPT","EDD","Exact"]):
        rows, total = results[key]
        with col:
            st.markdown(f"### {key}")
            st.caption(subtitles[key])
            st.metric("Total tardiness", f"{total:.2f}")
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    chart = pd.DataFrame({
        "Algorithm":list(results.keys()),
        "Total tardiness":[v[1] for v in results.values()]
    }).set_index("Algorithm")
    st.subheader("📊 Tardiness comparison")
    st.bar_chart(chart)
else:
    st.info("Press Run all algorithms to calculate the results.")

with st.expander("ℹ️ About this project"):
    st.markdown("""
    - **SPT:** sorts tasks by shortest execution time.
    - **EDD:** sorts tasks by earliest due date.
    - **Exact:** checks every possible order and chooses the minimum total tardiness.

    Assumptions: one machine, all tasks available at time zero, no preemption, and no setup times.
    Exact search has factorial complexity (`n!`), so this demo limits it to 9 tasks.
    """)
st.caption("TaskFlow Scheduler · Python + Streamlit")
