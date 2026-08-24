# Parent and Student Accounts

Family privacy is a core requirement.

## Roles
`admin`, `parent`, `student`

## Parent Privacy
Parent access is **deny-by-default**. A parent sees a student only through an explicit parent/student link. Server-side checks must deny unrelated student reports even if a user manually edits a URL.

## Parent Invitations
Invites can create a parent linked to one specific student or no student yet. The old all-students option was removed because it could expose unrelated grades.

## Adding Children
### Create a New Child
A parent can create a student account for ages 9–14; it is automatically linked to that parent.

### Family Link Code
An admin can generate a one-time, time-limited code for one existing student. Parents never receive a searchable directory of every student.

## Student Restrictions
Admins can independently disable account access, coursework, map access, or game access without deleting academic history.

## Password Management
Users can change their own passwords. Admins can reset passwords, issue temporary passwords, and require a change at next login. Plaintext passwords should not be stored in the database.

## Parent Assignments
Parents can assign coursework only to already-linked children. Assignment controls must never broaden grade visibility.
