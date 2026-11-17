# ai-sql-learning-assistant
# 🤖 AI SQL Learning Assistant

An AI-powered SQL learning application built with Python, Streamlit, MySQL, and OpenAI API. It helps users convert simple English questions into SQL queries, execute them, and understand the results.

## 🚀 Live Application

**Live Demo:**(https://ai-sql-learning-assistant-qhanwjwmrtd5zjjkneyysb.streamlit.app/).

## ✨ Features

- **AI SQL Generator:** Converts natural-language questions into SQL queries.
- **MySQL Integration:** Connects to a cloud-hosted MySQL database using Aiven.
- **Query Execution:** Executes supported SQL queries and displays results.
- **Query Explanation:** Helps users understand generated SQL.
- **Student Management:** Supports student record management.
- **Query History:** Tracks executed queries and their status.
- **SQL Safety:** Includes basic query validation and safety checks.

## 🛠️ Technologies Used

- Python
- SQL
- MySQL
- Streamlit
- OpenAI API
- Pandas
- MySQL Connector
- Git and GitHub
- Aiven Cloud MySQL

## 🏗️ Project Architecture

1. User enters a question in simple English.
2. OpenAI API generates an SQL query.
3. Python processes the generated query.
4. MySQL executes the supported query.
5. Streamlit displays the results.
6. Query history records execution details.

## 📂 Project Structure

```text
ai-sql-learning-assistant/
│
├── app.py
├── database.py
├── requirements.txt
├── README.md
└── .gitignore
```

## ⚙️ Installation

1. Clone the repository:

```bash
git clone https://github.com/Muskan36316/ai-sql-learning-assistant.git
```

2. Open the project folder:

```bash
cd ai-sql-learning-assistant
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure your database and OpenAI credentials securely using environment variables or Streamlit Secrets.

5. Run the application:

```bash
streamlit run app.py
```

## 🔐 Security

Never upload API keys, database passwords, `.env` files, or private certificates to GitHub.

## 👩‍💻 Developer

**Muskan**

Built as a personal learning project to explore Python development, SQL, database connectivity, and AI integration.

