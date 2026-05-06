# Smart Study Portal — Database Dump

**Generated:** 2026-04-24 09:50:15

---
## Users

| ID | Email | First Name | Last Name | Role | Active | Staff | Superuser |
|---|---|---|---|---|---|---|---|
| 1 | lakhabhayi@gmail.com | Sharma | Sharma | TEACHER | True | True | True |
| 2 | teacher_demo@example.com | Demo | Teacher | TEACHER | True | False | False |
| 3 | student1@example.com | Student | 1 | STUDENT | True | False | False |
| 4 | student2@example.com | Student | 2 | STUDENT | True | False | False |
| 5 | student3@example.com | Student | 3 | STUDENT | True | False | False |
| 6 | student4@example.com | Student | 4 | STUDENT | True | False | False |
| 7 | student5@example.com | Student | 5 | STUDENT | True | False | False |

---
## Classes

| ID | Name | Teacher (ID) | Teacher Email |
|---|---|---|---|
| 1 | Math 101 | 1 | lakhabhayi@gmail.com |
| 2 | Advanced Mathematics 101 | 2 | teacher_demo@example.com |

---
## Enrolments

| ID | Student Email | Student Name | Class | Class ID |
|---|---|---|---|---|
| 1 | student1@example.com | Student 1 | Advanced Mathematics 101 | 2 |
| 2 | student2@example.com | Student 2 | Advanced Mathematics 101 | 2 |
| 3 | student3@example.com | Student 3 | Advanced Mathematics 101 | 2 |
| 4 | student4@example.com | Student 4 | Advanced Mathematics 101 | 2 |
| 5 | student5@example.com | Student 5 | Advanced Mathematics 101 | 2 |
| 6 | student1@example.com | Student 1 | Math 101 | 1 |
| 7 | student2@example.com | Student 2 | Math 101 | 1 |

---
## Announcements

| ID | Class | Message | Sent At |
|---|---|---|---|
| 2 | Math 101 | Hello message.... | 2026-04-22 16:33:18.549629+00:00 |
| 1 | Advanced Mathematics 101 | Welcome to Demo Class! Please review the interactive syllabus modules before Fri | 2026-04-22 16:19:19.418524+00:00 |

---
## Quizzes

| ID | Title | Class | Status |
|---|---|---|---|
| 2 | Algebra Basics Validation | Advanced Mathematics 101 | DRAFT |
| 1 | Algebra Basics | Math 101 | LIVE |

---
## Questions

| ID | Quiz | Text | Options | Correct Index |
|---|---|---|---|---|
| 1 | Algebra Basics | What is 2+2? | ['2', '3', '4', '5'] | 2 |
| 2 | Algebra Basics Validation | What is 5 x 5? | ['10', '20', '25', '30'] | 2 |
| 3 | Algebra Basics Validation | What is the square root of 64? | ['6', '7', '8', '9'] | 2 |

---
## Quiz Submissions

*No submissions found.*

---
## Hand Raises

*No hand raises found.*

---
## Calendar Events

| ID | Class | Title | Event Date |
|---|---|---|---|
| 1 | Math 101 | Test 1 | 2026-04-22 22:03:00+00:00 |

---
## Summary

| Table | Count |
|---|---|
| Users | 7 |
| Classes | 2 |
| Enrolments | 7 |
| Announcements | 2 |
| Quizzes | 2 |
| Questions | 3 |
| Submissions | 0 |
| Hand Raises | 0 |
| Calendar Events | 1 |
