"""
Database Seeder Script
======================
Run this script to populate the database with sample data.

Usage:
    python seed.py
"""

import random
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Complaint, Response, Notification


def create_sample_users():
    """Create sample users including admins and students."""
    users = []
    
    # Super Admin
    super_admin = User(
        email='superadmin@university.edu.ng',
        full_name='Dr. Emeka Okafor',
        role='super_admin',
        department='ICT Department',
        phone='08011111111'
    )
    super_admin.set_password('SuperAdmin@123')
    users.append(super_admin)
    print('✓ Super Admin: superadmin@university.edu.ng / SuperAdmin@123')
    
    # Regular Admins
    admin_data = [
        ('admin1@university.edu.ng', 'Mrs. Funke Adeyemi', 'Student Affairs'),
        ('admin2@university.edu.ng', 'Mr. Chukwudi Eze', 'Bursary'),
        ('admin3@university.edu.ng', 'Mrs. Aisha Mohammed', 'Academic Affairs'),
    ]
    
    for email, name, dept in admin_data:
        admin = User(
            email=email,
            full_name=name,
            role='admin',
            department=dept,
            phone=f'0802{random.randint(1000000, 9999999)}'
        )
        admin.set_password('Admin@123')
        users.append(admin)
        print(f'✓ Admin: {email} / Admin@123')
    
    # Students
    student_data = [
        ('student1@university.edu.ng', 'Chioma Okonkwo', 'UNI/2021/001', 'Computer Science', 'Science'),
        ('student2@university.edu.ng', 'Adebayo Ogundimu', 'UNI/2021/002', 'Electrical Engineering', 'Engineering'),
        ('student3@university.edu.ng', 'Fatima Ibrahim', 'UNI/2020/003', 'Medicine', 'Health Sciences'),
        ('student4@university.edu.ng', 'Emeka Nwosu', 'UNI/2022/004', 'Accounting', 'Management Sciences'),
        ('student5@university.edu.ng', 'Grace Obi', 'UNI/2021/005', 'Law', 'Law'),
        ('student6@university.edu.ng', 'Mohammed Yusuf', 'UNI/2020/006', 'Economics', 'Social Sciences'),
        ('student7@university.edu.ng', 'Blessing Adekunle', 'UNI/2022/007', 'Nursing', 'Health Sciences'),
        ('student8@university.edu.ng', 'Tunde Bakare', 'UNI/2021/008', 'Civil Engineering', 'Engineering'),
        ('student9@university.edu.ng', 'Amina Bello', 'UNI/2020/009', 'Mass Communication', 'Arts'),
        ('student10@university.edu.ng', 'Chinedu Okoro', 'UNI/2022/010', 'Pharmacy', 'Pharmaceutical Sciences'),
    ]
    
    for email, name, matric, dept, faculty in student_data:
        student = User(
            email=email,
            full_name=name,
            matric_number=matric,
            department=dept,
            faculty=faculty,
            role='student',
            phone=f'0803{random.randint(1000000, 9999999)}'
        )
        student.set_password('Student@123')
        users.append(student)
    
    print(f'✓ Created {len(student_data)} students (password: Student@123)')
    
    return users


def create_sample_complaints(students, admins):
    """Create sample complaints."""
    complaints = []
    
    complaint_samples = [
        ('transcript', 'Request for Academic Transcript', 
         'I need my official transcript for my graduate school application. I completed my studies last year and require this document urgently for my application deadline next month.', 'high'),
        
        ('registration', 'Course Registration Error', 
         'I am unable to register for my required courses this semester. The system shows that I have an outstanding balance, but I have already cleared all my fees. Please help resolve this issue.', 'urgent'),
        
        ('fees_payment', 'Duplicate Payment Deduction', 
         'I was charged twice for my tuition fees. The payment was deducted from my account on two separate occasions. I have attached my bank statement as proof.', 'high'),
        
        ('accommodation', 'Hostel Allocation Issues', 
         'I applied for hostel accommodation last month but have not received any allocation. The semester has started and I am still without accommodation.', 'medium'),
        
        ('examination', 'Missing Exam Result', 
         'My result for CHM 201 is not showing on my portal. I sat for the examination and my name is on the attendance sheet. Please investigate.', 'high'),
        
        ('clearance', 'Final Year Clearance Delay', 
         'I have submitted all required documents for my final year clearance, but the process has been pending for over 3 weeks. I need this for my NYSC registration.', 'urgent'),
        
        ('scholarship', 'Scholarship Application Status', 
         'I applied for the merit scholarship 2 months ago but have not received any response. Kindly update me on the status of my application.', 'medium'),
        
        ('library', 'Library Card Not Working', 
         'My library card was recently renewed but it is not working at the entrance. I cannot access the library for my research work.', 'low'),
        
        ('id_card', 'Student ID Card Replacement', 
         'I lost my student ID card and need a replacement. What is the process and how long will it take?', 'medium'),
        
        ('course_registration', 'Unable to Add Required Course', 
         'The system is not allowing me to add ENG 301 which is a required course for my level. It says the course is full but it is mandatory.', 'high'),
        
        ('result_issues', 'Wrong Grade Recorded', 
         'My grade for MTH 201 is showing as D but I am sure I performed better. I request a review of my exam script.', 'high'),
        
        ('certificate', 'Certificate Collection Inquiry', 
         'I graduated in 2022 and would like to know when I can collect my certificate. What documents do I need to bring?', 'low'),
        
        ('admission', 'Admission Letter Not Received', 
         'I received a text message confirming my admission but have not received the official admission letter. My registration is due next week.', 'urgent'),
        
        ('medical', 'Medical Report Request', 
         'I need a copy of my medical report from the health center for my insurance claim. How do I go about this?', 'medium'),
        
        ('facilities', 'Broken Air Conditioner in Lecture Hall', 
         'The air conditioners in LT 5 have not been working for over a month. It is very uncomfortable during afternoon lectures.', 'low'),
    ]
    
    statuses = ['pending', 'in_progress', 'resolved', 'closed', 'pending', 'in_progress']
    
    for i, (category, title, description, priority) in enumerate(complaint_samples):
        # Pick a random student
        student = random.choice(students)
        
        # Random date within last 60 days
        days_ago = random.randint(1, 60)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        # Random status
        status = random.choice(statuses)
        
        # Set resolved_at for resolved/closed complaints
        resolved_at = None
        if status in ['resolved', 'closed']:
            resolved_at = created_at + timedelta(days=random.randint(1, 10))
        
        # Randomly assign some complaints
        assigned_to = None
        if status in ['in_progress', 'resolved', 'closed']:
            assigned_to = random.choice(admins).id if admins else None
        
        complaint = Complaint(
            user_id=student.id,
            category=category,
            title=title,
            description=description,
            priority=priority,
            status=status,
            assigned_to=assigned_to,
            created_at=created_at,
            resolved_at=resolved_at
        )
        
        complaints.append(complaint)
    
    print(f'✓ Created {len(complaints)} sample complaints')
    
    return complaints


def create_sample_responses(complaints, admins, students):
    """Create sample responses for complaints."""
    responses = []
    
    response_templates = [
        "Thank you for bringing this to our attention. We are looking into your case.",
        "Your complaint has been received and assigned to the appropriate department.",
        "We apologize for the inconvenience. We are working to resolve this issue.",
        "Please provide your receipt number for verification.",
        "Your issue has been resolved. Please confirm if everything is now working.",
        "We need additional information to process your request. Please visit our office.",
        "The matter has been escalated to the relevant authority for immediate action.",
        "Thank you for your patience. Your request is being processed.",
    ]
    
    for complaint in complaints:
        if complaint.status in ['in_progress', 'resolved', 'closed']:
            # Add admin response
            if admins:
                admin = random.choice(admins)
                response = Response(
                    complaint_id=complaint.id,
                    user_id=admin.id,
                    message=random.choice(response_templates),
                    is_internal=False,
                    created_at=complaint.created_at + timedelta(days=random.randint(1, 3))
                )
                responses.append(response)
                
                # Sometimes add student reply
                if random.random() > 0.5:
                    student_response = Response(
                        complaint_id=complaint.id,
                        user_id=complaint.user_id,
                        message="Thank you for your response. I will provide the required documents.",
                        is_internal=False,
                        created_at=complaint.created_at + timedelta(days=random.randint(4, 6))
                    )
                    responses.append(student_response)
    
    print(f'✓ Created {len(responses)} sample responses')
    
    return responses


def seed_database():
    """Main function to seed the database."""
    print('\n' + '=' * 50)
    print('    DATABASE SEEDER')
    print('=' * 50 + '\n')
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Drop and recreate tables
        print('Dropping existing tables...')
        db.drop_all()
        
        print('Creating new tables...')
        db.create_all()
        
        print('\nCreating users...')
        users = create_sample_users()
        db.session.add_all(users)
        db.session.commit()
        
        # Separate admins and students
        admins = [u for u in users if u.is_admin()]
        students = [u for u in users if u.role == 'student']
        
        print('\nCreating complaints...')
        complaints = create_sample_complaints(students, admins)
        db.session.add_all(complaints)
        db.session.commit()
        
        print('\nCreating responses...')
        responses = create_sample_responses(complaints, admins, students)
        db.session.add_all(responses)
        db.session.commit()
        
        print('\n' + '=' * 50)
        print('    DATABASE SEEDED SUCCESSFULLY!')
        print('=' * 50)
        print('\nYou can now log in with:')
        print('  Super Admin: superadmin@university.edu.ng / SuperAdmin@123')
        print('  Admin:       admin1@university.edu.ng / Admin@123')
        print('  Student:     student1@university.edu.ng / Student@123')
        print('')


if __name__ == '__main__':
    seed_database()