from flask import flash, render_template
from extensions import db
from models import Subject, Timetable, Teacher
from datetime import datetime, time, timedelta
import random

def calculate_time_slots(start_time_str, periods, period_duration, break_after, break_duration):
    """Calculate time slots based on parameters"""
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    time_slots = []
    current_time = datetime.combine(datetime.today(), start_time)

    for i in range(periods):
        if i == break_after:
            # Add break period
            end_time = current_time + timedelta(minutes=break_duration)
            time_slots.append(("Break", current_time.time(), end_time.time()))
            current_time = end_time
        
        end_time = current_time + timedelta(minutes=period_duration)
        time_slots.append((f"Period {i+1}", current_time.time(), end_time.time()))
        current_time = end_time

    return time_slots

def auto_generate_timetable(teacher_id, params):
    """
    Generate timetable based on provided parameters
    """
    try:
        # Get configuration parameters
        grade = params.get('grade')
        working_days = params.getlist('working_days')
        periods_per_day = int(params.get('periods_per_day', 6))
        break_after = int(params.get('break_after', 3))
        start_time = params.get('start_time', '09:00')
        period_duration = int(params.get('period_duration', 60))
        break_duration = int(params.get('break_duration', 60))
        avoid_consecutive = params.get('avoid_consecutive', True)
        balance_subjects = params.get('balance_subjects', True)

        # Get subjects for the teacher
        subjects = Subject.query.filter_by(teacher_id=teacher_id).all()
        if not subjects:
            return False, "No subjects found for this teacher"

        # Calculate time slots
        time_slots = calculate_time_slots(
            start_time, periods_per_day, period_duration, 
            break_after, break_duration
        )

        # Generate timetable
        timetable = []
        last_subject = {day: None for day in working_days}  # Track last subject for each day
        subject_counts = {subject.id: 0 for subject in subjects}  # Track subject distribution

        for day in working_days:
            daily_subjects = subjects.copy()
            random.shuffle(daily_subjects)
            subject_index = 0

            for slot_name, start, end in time_slots:
                if slot_name == "Break":
                    continue

                if subject_index >= len(daily_subjects):
                    random.shuffle(daily_subjects)
                    subject_index = 0

                # Select subject based on constraints
                selected_subject = None
                attempts = 0
                while attempts < len(daily_subjects):
                    candidate = daily_subjects[subject_index]
                    
                    # Check constraints
                    is_valid = True
                    if avoid_consecutive and last_subject[day] == candidate:
                        is_valid = False
                    if balance_subjects:
                        max_count = max(subject_counts.values()) if subject_counts.values() else 0
                        if subject_counts[candidate.id] > max_count:
                            is_valid = False

                    if is_valid:
                        selected_subject = candidate
                        break

                    subject_index = (subject_index + 1) % len(daily_subjects)
                    attempts += 1

                if not selected_subject:
                    selected_subject = daily_subjects[subject_index]

                # Create timetable entry
                entry = Timetable(
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    room=f"Room-{random.randint(101, 110)}",
                    teacher_id=teacher_id,
                    subject_id=selected_subject.id,
                    grade=grade
                )
                timetable.append(entry)
                
                # Update tracking variables
                last_subject[day] = selected_subject
                subject_counts[selected_subject.id] += 1
                subject_index = (subject_index + 1) % len(daily_subjects)

        return True, timetable

    except Exception as e:
        return False, f"Error generating timetable: {str(e)}"

def preview_timetable(teacher_id, params):
    """
    Generate a preview of the timetable without saving to database
    """
    success, result = auto_generate_timetable(teacher_id, params)
    if not success:
        return render_template('errors/500.html', error=result)

    timetable_entries = result
    time_slots = []
    days = params.getlist('working_days')

    # Group entries by day and time
    timetable_by_day = {day: [] for day in days}
    for entry in timetable_entries:
        timetable_by_day[entry.day_of_week].append(entry)
        if entry.start_time not in [slot[0] for slot in time_slots]:
            time_slots.append((entry.start_time, entry.end_time))
    
    time_slots.sort()

    return render_template(
        'teacher/_timetable_preview.html',
        timetable_by_day=timetable_by_day,
        time_slots=time_slots,
        days=days
    )

def save_timetable(teacher_id, params):
    """
    Save the generated timetable to database
    """
    try:
        # Clear existing entries
        grade = params.get('grade')
        Timetable.query.filter_by(teacher_id=teacher_id, grade=grade).delete()

        # Generate and save new timetable
        success, result = auto_generate_timetable(teacher_id, params)
        if not success:
            return False, result

        # Add all entries to database
        for entry in result:
            db.session.add(entry)

        db.session.commit()
        return True, "Timetable saved successfully!"

    except Exception as e:
        db.session.rollback()
        return False, f"Error saving timetable: {str(e)}"