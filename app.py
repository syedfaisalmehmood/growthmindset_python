import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import os
from fpdf import FPDF
import plotly.io as pio

# Initialize session state for tasks, if not already present
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame(columns=["Task ID", "Parent Task", "Subtask", "Description", "Due Date", "Assigned To", "Priority", "Status", "Start Date", "End Date", "Assignee Role", "Effort Hours", "Budget"])

# Initialize session state for team members (with roles)
if 'team_members' not in st.session_state:
    st.session_state.team_members = {
        "Faisal": "Project Manager",
        "Hamza": "Developer",
        "Huzaifa": "Designer",
        "Umer": "Tester"
    }

# Function to display tasks (used for showing the tasks after creation or updates)
def display_tasks():
    st.write("### List of Tasks")
    if st.session_state.tasks.empty:
        st.write("No tasks available.")
    else:
        # Display the tasks dataframe with relevant columns
        tasks_to_display = st.session_state.tasks[["Task ID", "Subtask", "Assigned To", "Priority", "Status", "Start Date", "End Date", "Effort Hours", "Budget"]]
        st.dataframe(tasks_to_display)

def scope_management():
    st.write("## Step 1: Scope Management")

    # Input fields for scope and deliverables
    scope = st.text_area("Define Scope of the Project")
    deliverables = st.text_area("List Project Deliverables (One per line)")

    if st.button("Set Scope and Deliverables"):
        st.session_state.scope = scope
        
        # Format the deliverables as a list (split by lines)
        deliverables_list = [item.strip() for item in deliverables.split("\n") if item.strip()]
        st.session_state.deliverables = deliverables_list  # Store deliverables in session state
        st.success("Project Scope and Deliverables have been set.")

    # Display saved scope and deliverables in a structured table format
    if 'scope' in st.session_state and 'deliverables' in st.session_state:
        # Create a DataFrame to display the deliverables in separate rows
        deliverables_data = {"Deliverables": [f"* {item}" for item in st.session_state.deliverables]}  # Changed bullet to *
        deliverables_df = pd.DataFrame(deliverables_data)

        # Display the Scope in a table with custom formatting
        st.write("### Project Scope and Deliverables:")

        # Display the Scope with custom formatting (bold, size 18)
        st.markdown(f"**<span style='font-size:18px'>{st.session_state.scope}</span>**", unsafe_allow_html=True)

        # Table for Deliverables
        if not deliverables_df.empty:
            st.table(deliverables_df)  # Display the list of deliverables as asterisks

# Function to create a main task
def create_main_task():
    st.write("## Create Main Task")
    
    # Main Task Inputs
    main_task_name = st.text_input("Main Task Name")
    description = st.text_area("Main Task Description")
    start_date = st.date_input("Main Task Start Date", min_value=datetime.today())
    end_date = st.date_input("Main Task End Date", min_value=datetime.today())
    assignee = st.selectbox("Assign Main Task To", list(st.session_state.team_members.keys()))
    role = st.session_state.team_members[assignee]
    priority = st.selectbox("Main Task Priority", ["Low", "Medium", "High"])
    status = st.selectbox("Main Task Status", ["Not Started", "In Progress", "Completed", "Blocked"])

    if st.button("Create Main Task"):
        main_task_id = len(st.session_state.tasks) + 1  # Create unique ID for the task
        new_main_task = pd.DataFrame([[main_task_id, None, main_task_name, description, end_date, assignee, priority, status, start_date, end_date, role, 0.0, 0.0]],
                                     columns=["Task ID", "Parent Task", "Subtask", "Description", "Due Date", "Assigned To", "Priority", "Status", "Start Date", "End Date", "Assignee Role", "Effort Hours", "Budget"] )
        # Add the new main task to the task DataFrame
        st.session_state.tasks = pd.concat([st.session_state.tasks, new_main_task], ignore_index=True)
        st.success(f"Main Task '{main_task_name}' created successfully!")

    # Display task list after creation
    display_tasks()

# Function to create a subtask under an existing main task
def create_subtask():
    st.write("## Create Subtask")

    # Select a main task
    main_task_names = st.session_state.tasks[st.session_state.tasks['Parent Task'].isna()]['Subtask'].tolist()
    if not main_task_names:
        st.write("No Main Tasks available. Please create a main task first.")
        return

    parent_task_name = st.selectbox("Select Parent Task", main_task_names)

    subtask_name = st.text_input(f"Subtask Name (for '{parent_task_name}')")
    subtask_description = st.text_area("Subtask Description")
    subtask_start_date = st.date_input("Subtask Start Date", min_value=datetime.today())
    subtask_end_date = st.date_input("Subtask End Date", min_value=datetime.today())
    subtask_assignee = st.selectbox("Assign Subtask To", list(st.session_state.team_members.keys()))
    subtask_role = st.session_state.team_members[subtask_assignee]
    subtask_priority = st.selectbox("Subtask Priority", ["Low", "Medium", "High"])
    subtask_status = st.selectbox("Subtask Status", ["Not Started", "In Progress", "Completed", "Blocked"])

    if st.button(f"Create Subtask under '{parent_task_name}'"):
        # Get the Parent Task ID from the selected main task
        parent_task_id = st.session_state.tasks[st.session_state.tasks['Subtask'] == parent_task_name]['Task ID'].values[0]
        subtask_id = len(st.session_state.tasks) + 1  # Create unique ID for subtask

        new_subtask = pd.DataFrame([[subtask_id, parent_task_id, subtask_name, subtask_description, subtask_end_date, subtask_assignee, subtask_priority, subtask_status, subtask_start_date, subtask_end_date, subtask_role, 0.0, 0.0]],
                                   columns=["Task ID", "Parent Task", "Subtask", "Description", "Due Date", "Assigned To", "Priority", "Status", "Start Date", "End Date", "Assignee Role", "Effort Hours", "Budget"])
        # Add the new subtask to the task DataFrame
        st.session_state.tasks = pd.concat([st.session_state.tasks, new_subtask], ignore_index=True)
        st.success(f"Subtask '{subtask_name}' created successfully under '{parent_task_name}'!")

    # Display task list after creation
    display_tasks()

# Resource Planning: Display main tasks and assign resources to subtasks
def resource_planning():
    st.write("## Resource Planning")
    
    # Select a parent task (main task)
    parent_task_names = st.session_state.tasks[st.session_state.tasks['Parent Task'].isna()]['Subtask'].tolist()
    
    if not parent_task_names:
        st.write("No Parent Tasks available. Please create a parent task first.")
        return
    
    parent_task_name = st.selectbox("Select Parent Task", parent_task_names)

    # Get the subtasks for the selected parent task (filter using Parent Task ID)
    parent_task_id = st.session_state.tasks[st.session_state.tasks['Subtask'] == parent_task_name]['Task ID'].values[0]
    subtasks = st.session_state.tasks[st.session_state.tasks['Parent Task'] == parent_task_id].reset_index(drop=True)

    if subtasks.empty:
        st.write(f"No subtasks available for the parent task '{parent_task_name}'.")
    else:
        st.write(f"### Assign Resources to Subtasks under '{parent_task_name}'")
        
        for index, subtask_row in subtasks.iterrows():
            subtask_name = subtask_row["Subtask"]
            # Add subtask dropdown for each subtask
            subtask_assignee = st.selectbox(f"Assign Resource to '{subtask_name}'", list(st.session_state.team_members.keys()), key=f"subtask_{subtask_row['Task ID']}")

            st.session_state.tasks.at[index, "Assigned To"] = subtask_assignee  # Update the resource in session state
            st.write(f"Assigned Resource: {subtask_assignee} (Role: {st.session_state.team_members[subtask_assignee]})")

# Budgeting (basic structure for budgeting)
def budgeting():
    st.write("## Budgeting")
    
    # Select a project (main task) for budgeting
    main_tasks = st.session_state.tasks[st.session_state.tasks['Parent Task'].isna()]
    
    if main_tasks.empty:
        st.write("No main tasks available for budgeting. Please create a main task first.")
        return

    project_names = main_tasks['Subtask'].tolist()
    project_name = st.selectbox("Select Project for Budgeting", project_names)

    # Budget input for the selected project
    estimated_cost = st.number_input("Enter Estimated Budget for Project", min_value=0.0, value=0.0)
    
    if st.button(f"Save Budget for '{project_name}'"):
        # Save the budget to the selected main task
        project_id = main_tasks[main_tasks['Subtask'] == project_name]['Task ID'].values[0]
        st.session_state.tasks.loc[st.session_state.tasks['Task ID'] == project_id, 'Budget'] = estimated_cost
        st.success(f"Budget of {estimated_cost} saved for project '{project_name}'.")

# Time Tracking (track effort hours for each subtask)
def time_tracking():
    st.write("## Time Tracking")
    
    # Ensure 'Task ID' column exists and select tasks
    if 'Task ID' not in st.session_state.tasks.columns:
        st.error("Missing 'Task ID' column. Please make sure tasks are created properly.")
        return
    
    # Display the list of tasks with effort hours
    tasks = st.session_state.tasks[['Task ID', 'Subtask', 'Assigned To', 'Effort Hours']]
    
    if tasks.empty:
        st.write("No tasks to track yet.")
    else:
        st.write("### Track Effort Hours")
        for index, task in tasks.iterrows():
            task_name = task['Subtask']
            current_hours = task['Effort Hours']
            
            # Display and update effort hours for each task
            hours_spent = st.number_input(f"Effort Hours for {task_name} (Assigned to {task['Assigned To']})", 
                                         min_value=0.0, value=current_hours, key=f"time_{task['Task ID']}")

            if st.button(f"Update Hours for {task_name}", key=f"update_{task['Task ID']}"):
                # Update the effort hours for the task
                st.session_state.tasks.at[index, 'Effort Hours'] = hours_spent
                st.success(f"Effort hours for task '{task_name}' updated to {hours_spent} hours!")

    # Display updated task list with effort hours
    display_tasks()

# Gantt Chart with Dependencies (using Plotly)
def gantt_chart():
    st.write("## Gantt Chart")
    fig = px.timeline(st.session_state.tasks, 
                       x_start="Start Date", 
                       x_end="End Date", 
                       y="Subtask", 
                       color="Priority", 
                       title="Project Timeline",
                       hover_name="Assigned To", 
                       hover_data=["Status", "Due Date", "Assignee Role"])
    fig.update_yaxes(categoryorder="total ascending")
    st.plotly_chart(fig)

# Reporting (Generates the project report in PDF)

def generate_report():
    st.write("## Generate Project Report")
    
    if st.session_state.tasks.empty:
        st.write("No tasks available to generate the report.")
        return
    
    # Ensure scope and deliverables are initialized
    if 'scope' not in st.session_state:
        st.session_state.scope = ""  # Initialize scope if not set
    if 'deliverables' not in st.session_state:
        st.session_state.deliverables = []  # Initialize deliverables if not set
    
    # Generate the Gantt Chart
    fig = px.timeline(st.session_state.tasks, 
                       x_start="Start Date", 
                       x_end="End Date", 
                       y="Subtask", 
                       color="Priority", 
                       title="Project Timeline",
                       hover_name="Assigned To", 
                       hover_data=["Status", "Due Date", "Assignee Role"])
    fig.update_yaxes(categoryorder="total ascending")
    
    # Save Gantt Chart to an image
    gantt_chart_path = "gantt_chart.png"
    pio.write_image(fig, gantt_chart_path)
    
    # Create the PDF report
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Set a simple font
    pdf.set_font("Arial", size=12)

    # Title
    pdf.cell(200, 10, txt="Project Management Report", ln=True, align="C")
    pdf.ln(10)  # Line break
    
    # Scope and Deliverables
    pdf.cell(200, 10, txt="Project Scope", ln=True)
    pdf.multi_cell(0, 10, "* This is a bullet point example.")  # Changed bullet to *
    pdf.ln(5)  # Line break
    
    # Add deliverables
    pdf.cell(200, 10, txt="Project Deliverables", ln=True)
    pdf.multi_cell(0, 10, "* This is a bullet point example.")  # Use the session state deliverables value
    pdf.ln(5)  # Line break

    # Task Details
    pdf.set_font('Arial', '', 12)
    pdf.cell(200, 10, txt="Task Details", ln=True)
    for index, task in st.session_state.tasks.iterrows():
        task_details = f"Task ID: {task['Task ID']}, Name: {task['Subtask']}, Assigned to: {task['Assigned To']}, Status: {task['Status']}, Start: {task['Start Date']}, End: {task['End Date']}, Budget: {task['Budget']}, Effort Hours: {task['Effort Hours']}"
        pdf.multi_cell(0, 10, task_details)
    
    # Add the Gantt Chart to the PDF
    pdf.ln(5)  # Line break
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="Gantt Chart", ln=True)
    pdf.ln(5)  # Line break
    pdf.image(gantt_chart_path, x=10, y=pdf.get_y(), w=180)  # Add Gantt chart image to the PDF

    # Save the PDF to a file
    pdf_output_path = "project_report.pdf"
    pdf.output(pdf_output_path)

    # Display success message and provide download link for the report
    st.success("Project report has been generated successfully!")
    st.download_button("Download Project Report", pdf_output_path)

# Main function to select project management steps
def main():
    st.title("Project Management Web Page")


    # Project Manager Info Section
    st.sidebar.header("Project Manager Info")
    project_manager = st.text_input("Project Manager Name", "Faisal")  # Default to Faisal
    st.sidebar.write(f"Project Manager: {project_manager}")
        
    # Display options for the user to choose which step of project management they want to work on
    menu = ["Scope Management", "Create Main Task", "Create Subtask", "Resource Planning", "Budgeting", "Time Tracking", "Gantt Chart", "Generate Project Report"]
    choice = st.sidebar.selectbox("Choose a Component", menu)

    
    if choice == "Scope Management":
        scope_management()
    elif choice == "Create Main Task":
        create_main_task()
    elif choice == "Create Subtask":
        create_subtask()
    elif choice == "Resource Planning":
        resource_planning()
    elif choice == "Budgeting":
        budgeting()
    elif choice == "Time Tracking":
        time_tracking()
    elif choice == "Gantt Chart":
        gantt_chart()
    elif choice == "Generate Project Report":
        generate_report()

if __name__ == "__main__":
    main()

