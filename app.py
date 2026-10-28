import os
import re
from pathlib import Path

import mysql.connector
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from database import get_connection, save_query_history


# -------------------- SETUP --------------------

load_dotenv(Path(__file__).resolve().parent / ".env")

st.set_page_config(
    page_title="AI SQL Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "query_results" not in st.session_state:
    st.session_state.query_results = None

if "query_history" not in st.session_state:
    st.session_state.query_history = []


# -------------------- DESIGN --------------------

st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp {
        background: radial-gradient(circle at top right, #25204d 0%, transparent 34%),
                    linear-gradient(135deg, #080d1b 0%, #10172b 55%, #17132f 100%);
        color: #f1f5ff;
    }
    [data-testid="stHeader"] { background: rgba(8, 13, 27, 0.72); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1020 0%, #12112a 100%);
        border-right: 1px solid #302952;
    }
    h1, h2, h3, p, label { color: #f1f5ff !important; }
    h2, h3 { letter-spacing: -0.3px; }
   .hero {
    padding: 14px 20px;
    border-radius: 14px;
    margin-bottom: 12px;
    }
    .hero-title {
    font-size: 25px;
    font-weight: 800;
    }
   .hero-subtitle {
    font-size: 13px;
    margin-bottom: 0;
    }
    .panel {
    background: #12182b;
    border: 1px solid #2d3452;
    border-radius: 12px;
    padding: 10px 14px;
    margin-bottom: 8px;
    }
    .small-note { color: #b8c0e5; font-size: 13px; }
    div[data-testid="stForm"] {
        background: rgba(19, 25, 47, 0.72);
        border: 1px solid #34385e;
        padding: 18px;
        border-radius: 16px;
    }
    .stApp div[data-testid="stFormSubmitButton"] button,
    .stApp div[data-testid="stButton"] button {
        background: linear-gradient(90deg, #6d28d9, #9333ea) !important;
        color: #ffffff !important;
        border: 1px solid #a78bfa !important;
        border-radius: 12px !important;
        min-height: 44px;
        font-size: 15px !important;
        font-weight: 700 !important;
        box-shadow: 0 5px 15px rgba(124, 58, 237, 0.20);
    }
    .stApp div[data-testid="stFormSubmitButton"] button:hover,
    .stApp div[data-testid="stButton"] button:hover {
        background: linear-gradient(90deg, #7c3aed, #a855f7) !important;
        border-color: #c4b5fd !important;
    }
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        background: #111a30;
        border: 1px solid #45416d;
        border-radius: 11px;
    }
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
    background-color: #111a30 !important;
    border: 1px solid #45416d !important;
    border-radius: 11px;
    }
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    caret-color: #ffffff !important;
    background-color: transparent !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #3b4166;
        border-radius: 14px;
        overflow: hidden;
    }
    [data-testid="stMetric"] {
        background: rgba(25, 33, 59, 0.82);
        border: 1px solid #34385e;
        border-radius: 14px;
        padding: 14px 16px;
    }
    [data-testid="stCode"] {
        border: 1px solid #3b3265;
        border-radius: 12px;
    }
    [data-testid="stAlert"] { border-radius: 12px; }
    /* Reduce vertical spacing */
    div[data-testid="stVerticalBlock"] {
    gap: 0.75rem;
    }

    /* Compact headings */
    h2, h3 {
    margin-top: 0.4rem !important;
    margin-bottom: 0.4rem !important;
    }

    /* Compact SQL code block */
    div[data-testid="stCode"] {
    margin-bottom: 0.3rem;
    }
    
/* Example questions: brighter text */
.example-questions,
.example-questions li {
    color: #F1F5F9 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}

/* Sidebar text visibility */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li {
    color: #F1F5F9 !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## 🤖 SQL Assistant")
    st.caption("AI-powered database learning")
    st.markdown("---")
    st.markdown("### Navigation")

    page = st.radio(
        "Go to",
        [
            "🧠 AI SQL Generator",
            "🗄️ MySQL Database",
            "📊 Query Results",
            "🕘 Query History",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### Example questions")
    st.markdown("- Show all students")
    st.markdown("- Show students with marks greater than 80")
    st.markdown("- Show IT students")
    st.markdown("- Show students from Mumbai")
    st.markdown("---")
    st.caption("Built with Python • Streamlit • MySQL • OpenAI")


# -------------------- AI SQL GENERATOR --------------------

if page == "🧠 AI SQL Generator":
    st.markdown(
        """
        <div class="hero">
            <div class="hero-title">✨ AI SQL Learning Assistant</div>
            <p class="hero-subtitle">
                Ask questions in simple English. Generate SQL and explore your data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="panel">🤖 <b>AI Assistant</b><br>'
            '<span class="small-note">Natural language to SQL</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="panel">🗄️ <b>Database</b><br>'
            '<span class="small-note">MySQL • students</span></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="panel">🛡️ <b>Query Safety</b><br>'
            '<span class="small-note">SELECT statements only</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### 💬 Ask your SQL question")

    with st.form("sql_question_form"):
        question = st.text_input(
            "Your question",
            placeholder="e.g. Show students with marks greater than 80",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("✨ Generate SQL & Run Query")

    if submitted:
        if not question.strip():
            st.warning("Please enter a question first.")
        elif not os.getenv("OPENAI_API_KEY"):
            st.error("OpenAI API key not found. Check your .env file.")
        else:
            try:
                with st.spinner("🤖 AI is generating your SQL query..."):
                    client = OpenAI()
                    response = client.responses.create(
                        model="gpt-6-luna",
                        
instructions="""
You are an expert MySQL teacher for beginners.

Convert the user's question into exactly ONE valid MySQL SELECT query.

The only supported table is students.
Its columns are:
id, name, age, marks, department, city.

Supported features:
WHERE, AND, OR, NOT, IN, BETWEEN, LIKE, ORDER BY,
ASC, DESC, LIMIT, COUNT, AVG, SUM, MAX, MIN, GROUP BY, HAVING.

Rules:
1. Generate only one SELECT query.
2. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE,
   or any other modifying query.
3. Never use JOIN, UNION, subqueries, or other tables.
4. If the user explicitly asks for a table other than students,
   do not silently replace that table with students.
5. For an unsupported table, return exactly:
   UNSUPPORTED_TABLE
6. Do not include explanations or Markdown code fences.
7. Return valid MySQL syntax only, except for the required
   UNSUPPORTED_TABLE response.
8. If the user's request asks to insert, update, delete,
   drop, alter, create, or modify data or database structure,
   return exactly:
   UNSUPPORTED_OPERATION
""",
                        input=question,
                    )

                query = response.output_text.strip()
                # Block requests that ask to modify data.
                if re.search(
                    r"\b(delete|remove|drop|truncate|update|insert|alter|"
                    r"modify|erase|clear)\b",
                    question,
                    re.IGNORECASE,
                ):
                    try:
                        save_query_history(question, 0, "Failed")
                    except Exception as history_error:
                        st.warning("Failed query history could not be saved.")
                        st.caption(f"History error: {history_error}")
                        st.session_state.query_history.insert(
                            0,
                            {
                                "query": question,
                                "rows": 0,
                                "status": "Failed",
                                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                            },
                        )
                    st.error(
                            "Operation blocked! The AI SQL generator only supports SELECT queries." 
                            " No data changes were made."
                        )
                    st.stop()
                query = re.sub(
                    r"^```(?:sql)?\s*|\s*```$",
                    "",
                    query,
                    flags=re.IGNORECASE,
                ).strip()

                normalized = query.strip()
                if normalized.endswith(";"):
                    normalized = normalized[:-1].strip()
                    
                # Handle unsupported tables before SQL safety validation.
                if normalized.strip().upper() == "UNSUPPORTED_TABLE":
                    try:
                        save_query_history(question, 0, "Failed")
                    except Exception as history_error:
                        st.warning("The Failed query history could not be saved..")
                        st.caption(f"History error: {history_error}")

                    st.session_state.query_history.insert(
                        0,
                        {
                            "query": question,
                            "rows": 0,
                            "status": "Failed",
                            "timestamp": pd.Timestamp.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        },
                    )

                    st.error(
                        "Operation blocked! The AI SQL generator only supports SELECT queries." 
                        " No data changes were made."
                    )
                    st.stop()

                # Basic safety validation for read-only SQL.
                unsafe_query = (
                    not re.match(r"^SELECT\b", normalized, re.IGNORECASE)
                    or ";" in normalized
                    or "--" in normalized
                    or "/*" in normalized
                    or "*/" in normalized
                    or "#" in normalized
                    or re.search(
                        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|"
                        r"REPLACE|GRANT|REVOKE|CALL|EXEC|INTO|LOAD_FILE|"
                        r"OUTFILE|DUMPFILE)\b",
                        normalized,
                        re.IGNORECASE,
                    )
                    or not re.search(
                        r"\bFROM\s+students?\b",
                        normalized,
                        re.IGNORECASE,
                    )
                    or re.search(
                        r"\b(JOIN|UNION|WITH)\b",
                        normalized,
                        re.IGNORECASE,
                    )
                )

                if unsafe_query:
                    try:
                        save_query_history(question, 0, "Failed")
                    except Exception as history_error:
                        st.warning("Failed query history could not be saved.")
                        st.caption(f"History error: {history_error}")
                        
                        st.session_state.query_history.insert(
                            0,
                            {
                                "query": question,
                                "rows": 0,
                                "status": "Failed",
                                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                                },
                        )

                        st.error(
                            "Safety check failed. This query cannot be executed. "
                            "Please try a simpler question about the students table."
                            )
                else:
                    # Step 1: Show generated SQL.
                    st.markdown("### 💻 1. Generated SQL")
                    st.code(normalized + ";", language="sql")

                    # Step 2: Run query and show results BEFORE the explanation.
                    st.markdown("### 📊 2. Query Results")
                    connection = None
                    cursor = None
                    rows = []
                    columns = []

                    try:
                        with st.spinner("🗄️ Fetching results from MySQL..."):
                            connection = get_connection()
                            cursor = connection.cursor()
        
                            cursor.execute(normalized)
                            rows = cursor.fetchall()
                            columns = [col[0] for col in cursor.description]

                        df = pd.DataFrame(rows, columns=columns)
                        st.session_state.query_results = df

                        try:
                            save_query_history(normalized, len(rows), "Success")
                        except Exception as history_error:
                            st.warning(
                                "Query ran, but it could not be saved to history."
                            )
                            st.caption(f"History error: {history_error}")

                        st.session_state.query_history.insert(
                            0,
                            {
                                "query": normalized,
                                "rows": len(rows),
                                "status": "Success",
                                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                            },
                        )

                        if not df.empty:
                            r1, r2 = st.columns(2)
                            with r1:
                                st.metric("Rows returned", len(df))
                            with r2:
                                st.metric("Columns", len(columns))
                            st.dataframe(
                                df,
                                use_container_width=True,
                                hide_index=True,
                            )
                            st.success("Query executed successfully!")
                        else:
                            st.info(
                                "Query ran successfully, but no records were found."
                            )

                    except mysql.connector.Error as db_error:
                        # Record the failed SQL query in the persistent MySQL history.
                        try:
                            save_query_history(normalized, 0, "Failed")
                        except Exception as history_error:
                            st.warning("Failed query history could not be saved.")
                            st.caption(f"History error: {history_error}")

                        # Keep the failed query visible in this Streamlit session too.
                        st.session_state.query_history.insert(
                            0,
                            {
                                "query": normalized,
                                "rows": 0,
                                "status": "Failed",
                                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                            },
                        )

                        st.error("MySQL query could not be executed.")
                        st.caption(f"Database details: {db_error}")
                    finally:
                        if cursor is not None:
                            try:
                                cursor.close()
                            except mysql.connector.Error:
                                pass
                        if connection is not None:
                            try:
                                connection.close()
                            except mysql.connector.Error:
                                pass

                    # Step 3: Explanation appears after the results.
                    st.markdown("### 🧠 3. Understand This Query")
                    with st.spinner("AI is explaining the SQL query..."):
                        explanation_response = client.responses.create(
                            model="gpt-6-luna",
                            instructions="""
You are a friendly SQL teacher for beginners.
Explain the given MySQL SELECT query in simple English.

Use exactly these three Markdown headings, each on a separate line:
### 1. What this query does
### 2. How it works, step by step
### 3. Important SQL keywords

Rules:
- Use proper Markdown formatting.
- Do not put the explanation inside a code block.
- Use bullet points under headings 2 and 3.
- Keep the explanation short and beginner-friendly.
- Do not generate another SQL query.
""",
                            input=f"User question: {question}\nSQL query: {normalized}",
                        )
                    st.markdown("### ✨ Query Explanation")
                    st.markdown(explanation_response.output_text)

            except Exception as error:
                st.error("Query process karte waqt error aaya.")
                st.caption(f"Error details: {error}")


# -------------------- STUDENT MANAGEMENT --------------------

elif page == "🗄️ MySQL Database":
    st.markdown("## 🎓 Student Management")
    st.caption("Manage student records from your MySQL database.")

    # Load student records from MySQL
    connection = None
    cursor = None
    students = []

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, age, marks, department, city
            FROM students
            ORDER BY id
        """)
        students = cursor.fetchall()

    except mysql.connector.Error as error:
        st.error("Student records could not be loaded.")
        st.caption(f"Database details: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

    # Dashboard summary cards
    total_students = len(students)
    average_marks = (
        sum(float(s["marks"] or 0) for s in students) / total_students
        if total_students else 0
    )
    departments = len(set(
        s["department"] for s in students if s["department"]
    ))

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("👨‍🎓 Total Students", total_students)

    with c2:
        st.metric("📊 Average Marks", f"{average_marks:.1f}")

    with c3:
        st.metric("🏢 Departments", departments)

    st.markdown("---")

    # Student list and search
    st.markdown("### 📋 Student List")

    search_text = st.text_input(
        "🔎 Search students",
        placeholder="Search by name, ID, department or city...",
        key="student_search",
    )

    filtered_students = [
        s for s in students
        if search_text.strip().lower() in " ".join(
            str(s.get(key) or "")
            for key in ["id", "name", "age", "marks", "department", "city"]
        ).lower()
    ]

    if filtered_students:
        student_df = pd.DataFrame(filtered_students)
        student_df.columns = [
            "Student ID", "Name", "Age", "Marks", "Department", "City"
        ]
        st.dataframe(
            student_df,
            use_container_width=True,
            hide_index=True,
        )
        st.caption(f"Showing {len(filtered_students)} of {total_students} students.")
    else:
        st.info("No students found. Try another search or add a student.")

    st.markdown("---")

    # Add student form
    with st.expander("➕ Add New Student", expanded=False):
        with st.form("add_student_form", clear_on_submit=True):
            new_id = st.number_input(
                "Student ID", min_value=1, step=1, key="new_student_id"
            )
            new_name = st.text_input("Student Name", key="new_student_name")
            new_age = st.number_input(
                "Age", min_value=1, max_value=100, value=20,
                key="new_student_age"
            )
            new_marks = st.number_input(
                "Marks", min_value=0, max_value=100, value=75,
                key="new_student_marks"
            )
            new_department = st.selectbox(
                "Department",
                ["IT", "Finance", "Marketing", "HR", "Other"],
                key="new_student_department"
            )
            new_city = st.text_input("City", key="new_student_city")

            add_clicked = st.form_submit_button("➕ Add Student")

        if add_clicked:
            if not new_name.strip() or not new_city.strip():
                st.warning("Please enter the student's name and city.")
            else:
                connection = None
                cursor = None
                try:
                    connection = get_connection()
                    cursor = connection.cursor()
                    cursor.execute("""
                        INSERT INTO students
                        (id, name, age, marks, department, city)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        int(new_id), new_name.strip(), int(new_age),
                        int(new_marks), new_department, new_city.strip()
                    ))
                    connection.commit()
                    st.success("Student added successfully!")
                    st.rerun()

                except mysql.connector.Error as error:
                    st.error(
                        "Student could not be added. "
                        "The student ID already exists, or there is a database error."
                    )

                    st.caption(f"Database details: {error}")
                finally:
                    if cursor is not None:
                        cursor.close()
                    if connection is not None:
                        connection.close()

    # Update and delete require an existing student
    if students:
        st.markdown("### 🛠️ Update or Delete Student")

        student_ids = [int(s["id"]) for s in students]
        selected_id = st.selectbox(
            "Select Student",
            student_ids,
            format_func=lambda sid: next(
                f'{s["id"]} — {s["name"]}'
                for s in students if int(s["id"]) == sid
            ),
            key="manage_student_id",
        )

        selected_student = next(
            s for s in students if int(s["id"]) == selected_id
        )

        update_tab, delete_tab = st.tabs(
            ["✏️ Update Student", "🗑️ Delete Student"]
        )

        with update_tab:
            with st.form("update_student_form"):
                edit_name = st.text_input(
                    "Student Name", value=str(selected_student["name"] or "")
                )
                edit_age = st.number_input(
                    "Age", min_value=1, max_value=100,
                    value=int(selected_student["age"] or 20)
                )
                edit_marks = st.number_input(
                    "Marks", min_value=0, max_value=100,
                    value=int(selected_student["marks"] or 0)
                )

                departments_list = [
                    "IT", "Finance", "Marketing", "HR", "Other"
                ]
                current_department = selected_student["department"] or "Other"
                department_index = (
                    departments_list.index(current_department)
                    if current_department in departments_list else 4
                )
                edit_department = st.selectbox(
                    "Department",
                    departments_list,
                    index=department_index,
                )
                edit_city = st.text_input(
                    "City", value=str(selected_student["city"] or "")
                )

                update_clicked = st.form_submit_button(
                    "💾 Save Changes"
                )

            if update_clicked:
                if not edit_name.strip() or not edit_city.strip():
                    st.warning("Name and city cannot be blank.")
                else:
                    connection = None
                    cursor = None
                    try:
                        connection = get_connection()
                        cursor = connection.cursor()
                        cursor.execute("""
                            UPDATE students
                            SET name = %s, age = %s, marks = %s,
                                department = %s, city = %s
                            WHERE id = %s
                        """, (
                            edit_name.strip(), int(edit_age),
                            int(edit_marks), edit_department,
                            edit_city.strip(), selected_id
                        ))
                        connection.commit()
                        st.success("Student updated successfully!")
                        st.rerun()

                    except mysql.connector.Error as error:
                        st.error("Student could not be updated.")
                        st.caption(f"Database details: {error}")
                    finally:
                        if cursor is not None:
                            cursor.close()
                        if connection is not None:
                            connection.close()

        with delete_tab:
            st.warning(
                f"Selected student: {selected_student['name']} "
                f"(ID: {selected_id}). Deletion cannot be undone."
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this student.",
                key="confirm_student_delete",
            )

            if st.button("🗑️ Delete Student", key="delete_student_button"):
                if not confirm_delete:
                    st.warning("Please confirm deletion first.")
                else:
                    connection = None
                    cursor = None
                    try:
                        connection = get_connection()
                        cursor = connection.cursor()
                        cursor.execute(
                            "DELETE FROM students WHERE id = %s",
                            (selected_id,)
                        )
                        connection.commit()

                        if cursor.rowcount:
                            st.success("Student deleted successfully!")
                        else:
                            st.info("Student record was not found.")

                        st.rerun()

                    except mysql.connector.Error as error:
                        st.error("Student could not be deleted.")
                        st.caption(f"Database details: {error}")
                    finally:
                        if cursor is not None:
                            cursor.close()
                        if connection is not None:
                            connection.close()
    else:
        st.info("No student records available. Add your first student above.")

# -------------------- QUERY RESULTS PAGE --------------------

elif page == "📊 Query Results":
    st.markdown("## 📊 Query Results")
    df = st.session_state.query_results
    if df is not None:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Please run a query first from AI SQL Generator.")



# -------------------- QUERY HISTORY PAGE --------------------

elif page == "🕘 Query History":
    st.markdown("## 🕘 Query History")
    st.caption("Search and review your previously executed SQL queries.")

    # Search controls
    search_text = st.text_input(
        "🔎 Search query history",
        placeholder="Search SQL query, status or date...",
        key="history_search",
    )

    status_filter = st.selectbox(
        "Filter by status",
        ["All", "Success", "Failed"],
        key="history_status_filter",
    )

    # Load saved history from MySQL
    connection = None
    cursor = None
    history_records = []

    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT query_text, rows_returned, status, created_at
            FROM query_history
            ORDER BY created_at DESC
        """)

        history_records = cursor.fetchall()

    except mysql.connector.Error as error:
        st.error("Query history could not be loaded from the database..")
        st.caption(f"Database details: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()

    # Filter the records
    filtered_history = []

    for item in history_records:
        query_text = str(item.get("query_text") or "")
        status = str(item.get("status") or "Unknown")
        timestamp = str(item.get("created_at") or "")
        rows = item.get("rows_returned", 0)

        searchable_text = f"{query_text} {status} {timestamp}".lower()

        matches_search = search_text.strip().lower() in searchable_text
        matches_status = (
            status_filter == "All"
            or status.lower() == status_filter.lower()
        )

        if matches_search and matches_status:
            filtered_history.append({
                "Timestamp": timestamp,
                "SQL Query": query_text,
                "Status": status,
                "Rows Returned": rows,
            })

    # Summary
    total_queries = len(history_records)
    successful_queries = sum(
        1 for item in history_records
        if str(item.get("status", "")).lower() == "success"
    )
    failed_queries = sum(
        1 for item in history_records
        if str(item.get("status", "")).lower() == "failed"
    )

    c1, c2, c3 = st.columns(3)

    c1.metric("🧾 Total Queries", total_queries)
    c2.metric("✅ Successful", successful_queries)
    c3.metric("❌ Failed", failed_queries)

    st.markdown("---")
    st.markdown("### 📋 Query Records")

    if filtered_history:
        history_df = pd.DataFrame(filtered_history)

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            f"Showing {len(filtered_history)} of {total_queries} records."
        )

        with st.expander("💻 View SQL query details"):
            for i, item in enumerate(filtered_history, start=1):
                st.markdown(f"**Query {i} — {item['Status']}**")
                st.caption(f"Timestamp: {item['Timestamp']}")
                st.code(item["SQL Query"], language="sql")
                st.caption(f"Rows returned: {item['Rows Returned']}")
    else:
        st.info("No matching query history found.")