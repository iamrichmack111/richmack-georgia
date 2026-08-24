# Richmack Georgia — Phase 4 (v0.4)

Phase 4 adds family administration, unified grades, usage analytics, improvement recommendations, and account controls to the Phase 3.1 Georgia Studies curriculum platform.

## Phase 4 additions

- **Game grades in the gradebook:** Map Hunt attempts now appear beside coursework in Admin → Latest Gradebook Activity and in CSV exports.
- **Student analytics:** coursework average, lessons mastered, game average/best score, active days, recorded learning time, recent activity, and improvement recommendations.
- **Parent accounts:** admins can generate seven-day one-use parent invitation links.
- **Scoped parent access:** an invite can be linked to one student or all current students. After registration, Admin → Users can change exactly which students each parent may view.
- **Parent portal:** parents see only linked students and can open their grades, games, usage, tips, and CSV export.
- **User management:** create student, parent, or admin accounts; disable/enable accounts; restrict student coursework, map, and games separately.
- **Password controls:** every user can change their own password. Admins can reset any user's password to a temporary password and force a change on next login.
- **Bulk password reset:** resets every active account except the currently logged-in administrator and downloads a one-time CSV containing the generated temporary passwords.
- Existing Phase 3 curriculum, 85% mastery, constructed-response review, Phase 2 atlas, and Map Hunt remain included.

## Local install

```bash
cd ~/Downloads
unzip richmack-georgia-v0.4.zip
cd richmack-georgia-v0.4

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
set -a
source .env
set +a

python run.py
```

Open `http://127.0.0.1:5075`.

### Default test accounts

- Admin: `admin` / `change-me-local`
- Student age 12: `student` / `student`
- Student age 14: `student14` / `student14`

## Test the missing 90% game grade fix

1. Sign in as `student14`.
2. Play Map Hunt and submit a score.
3. Log out and sign in as `admin`.
4. Open **Admin**.
5. Under **Latest Gradebook Activity**, the Map Hunt result should appear as `Game` with its score.
6. The student's row also shows game average and number of game attempts.
7. Open the student's **Analytics** report for improvement tips and usage statistics.
8. Export All Grades CSV; the game attempt appears with `record_type=game`.

## Parent invitation test on the same Mac

1. Sign in as admin.
2. Open **Admin → Parent Invite Link**.
3. Choose the student the parent is allowed to view, then click **Create Invite Link**.
4. Copy the generated link and open it in a private/incognito browser window.
5. Register the parent account.
6. The parent is sent to the Parent Portal after login and can view only linked students.

## Parent invitation test from another device on the same Wi-Fi

A `127.0.0.1` invite points back to the device opening the link, so it cannot be used by another computer or phone. For LAN testing, run the server on all interfaces:

```bash
cd ~/Downloads/richmack-georgia-v0.4
source .venv/bin/activate

export HOST=0.0.0.0
python run.py
```

Find your Mac's local IP:

```bash
ipconfig getifaddr en0
```

If Wi-Fi is not `en0`, try:

```bash
ipconfig getifaddr en1
```

Suppose it returns `192.168.1.50`. On the Mac and the other device, open:

```text
http://192.168.1.50:5075
```

Create the parent invite while you are using that LAN address. The generated invite will then use the same reachable host. The other device must be on the same local network, and macOS may ask whether Python may accept incoming connections.

When deployed to the cloud, invite links will use the application's normal public HTTPS hostname instead.

## Restricting users

Admin → **Users** allows you to:

- Disable an account completely.
- Allow/deny a student access to coursework.
- Allow/deny a student access to the map.
- Allow/deny a student access to games.
- Change which students a parent can view.
- Reset an individual password.
- Create new users.
- Bulk-reset active user passwords.

## Password behavior

A user can change their own password from **Password** in the navigation.

When an administrator resets a password, that password is temporary. The next successful login forces the account through **Change Password** before continuing.

For a bulk reset, save the downloaded CSV immediately. The application stores password hashes, not readable copies of the generated temporary passwords.

## Verification

```bash
source .venv/bin/activate
pytest -q
curl -s http://127.0.0.1:5075/health
```

Expected health response includes:

```json
{"app":"richmack-georgia","phase":"4.0","status":"ok"}
```

## Source policy

Course material continues to use the built-in verified source registry containing official Georgia Department of Education, Georgia EPD, GDOT, Georgia Ports Authority, and U.S. Census sources. Simplified numerical scenarios used for teaching are identified as instructional scenarios rather than real operational rates.
