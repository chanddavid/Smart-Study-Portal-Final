// ============================================================
// Smart Study Portal — Application Controller
// ============================================================

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const screens = {
    login: $('#login-section'),
    dashboard: $('#dashboard'),
    classView: $('#classroom-view')
};

let activeClassId = null;
let currentRole = null;
let ws = null;

// ---- Utilities ----
function showToast(message, type = 'success') {
    const c = $('#toast-container');
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.textContent = message;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; setTimeout(() => t.remove(), 300); }, 3000);
}

function switchScreen(key) {
    Object.values(screens).forEach(s => s.classList.add('hidden'));
    screens[key].classList.remove('hidden');
}

function fmtDate(d) {
    return new Date(d).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function fmtTime(d) {
    return new Date(d).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

function statusBadge(s) {
    const map = { DRAFT: 'badge-draft', LIVE: 'badge-live', COMPLETED: 'badge-completed' };
    return `<span class="badge ${map[s] || 'badge-default'}">${s}</span>`;
}

// ---- Tabs ----
$$('.tab').forEach(tab => {
    tab.addEventListener('click', e => {
        $$('.tab').forEach(t => t.classList.remove('active'));
        $$('.tab-content').forEach(c => c.classList.remove('active'));
        e.target.classList.add('active');
        $('#' + e.target.dataset.target).classList.add('active');
        refreshActiveTab();
    });
});

function refreshActiveTab() {
    const id = $('.tab-content.active')?.id;
    if (id === 'tab-feed') fetchAnnouncements();
    if (id === 'tab-roster') fetchRoster();
    if (id === 'tab-quizzes') fetchQuizzes();
    if (id === 'tab-calendar') fetchCalendar();
}

// ---- Auth ----
window.addEventListener('auth_expired', () => { showToast('Session expired.', 'error'); switchScreen('login'); });

$('#login-form').addEventListener('submit', async e => {
    e.preventDefault();
    const btn = $('#login-btn');
    btn.disabled = true; btn.textContent = 'Signing in...';
    try {
        const res = await ApiClient.login($('#login-email').value, $('#login-password').value);
        ApiClient.setToken(res.access);
        localStorage.setItem('ssp_user', JSON.stringify(res.user));
        showToast(`Welcome back, ${res.user.first_name}!`);
        initDashboard();
    } catch (err) {
        showToast(err.data?.detail || 'Invalid credentials.', 'error');
    } finally {
        btn.disabled = false; btn.textContent = 'Sign In';
    }
});

$('#logout-btn').addEventListener('click', async () => {
    // Show confirmation modal
    $('#logout-confirm-modal').classList.remove('hidden');
});

$('#btn-confirm-logout').addEventListener('click', async () => {
    try { await ApiClient.logout(); } catch (_) {}
    ApiClient.clearAuth();
    if (ws) ws.close();
    // remove the confirm logout modal
    $('#logout-confirm-modal').classList.add('hidden');

    switchScreen('login');
    showToast('Logged out.', 'info');
});
// Cancel logout
$('#btn-cancel-logout').addEventListener('click', () => $('#logout-confirm-modal').classList.add('hidden'));

// ---- Password Reset Flow ----
$('#link-forgot-pw').addEventListener('click', e => {
    e.preventDefault();
    $('#pw-reset-request-modal').classList.remove('hidden');
});
$('#btn-cancel-pw-request').addEventListener('click', () => $('#pw-reset-request-modal').classList.add('hidden'));
$('#btn-cancel-pw-confirm').addEventListener('click', () => $('#pw-reset-confirm-modal').classList.add('hidden'));

$('#pw-reset-request-form').addEventListener('submit', async e => {
    e.preventDefault();
    try {
        const res = await ApiClient.resetPasswordRequest($('#pw-reset-email').value);
        showToast('Reset code generated! Enter your new password below.', 'info');
        $('#pw-reset-request-modal').classList.add('hidden');
        // Auto-fill UID and TOKEN from response (no email service)
        $('#pw-reset-uid').value = res.uid || '';
        $('#pw-reset-token').value = res.token || '';
        $('#pw-reset-confirm-modal').classList.remove('hidden');
    } catch (err) {
        showToast(err.data?.detail || 'Email not found.', 'error');
    }
});

$('#pw-reset-confirm-form').addEventListener('submit', async e => {
    e.preventDefault();
    try {
        await ApiClient.resetPasswordConfirm(
            $('#pw-reset-uid').value,
            $('#pw-reset-token').value,
            $('#pw-reset-newpw').value
        );
        showToast('Password reset successful! You can now sign in.', 'success');
        $('#pw-reset-confirm-modal').classList.add('hidden');
        // Clear fields
        $('#pw-reset-email').value = '';
        $('#pw-reset-uid').value = '';
        $('#pw-reset-token').value = '';
        $('#pw-reset-newpw').value = '';
    } catch (err) {
        showToast(err.data?.detail || 'Invalid token.', 'error');
    }
});

// ---- Edit Profile ----
$('#btn-edit-profile').addEventListener('click', () => {
    const user = ApiClient.getUser();
    if (!user) return;
    $('#profile-first-name').value = user.first_name;
    $('#profile-last-name').value = user.last_name;
    $('#profile-phone').value = user.phone_number || '';
    $('#profile-address').value = user.address || '';
    $('#edit-profile-modal').classList.remove('hidden');
});
$('#btn-cancel-profile').addEventListener('click', () => $('#edit-profile-modal').classList.add('hidden'));

$('#edit-profile-form').addEventListener('submit', async e => {
    e.preventDefault();
    const first_name = $('#profile-first-name').value.trim();
    const last_name = $('#profile-last-name').value.trim();
    const phone_number = $('#profile-phone').value.trim();
    const address = $('#profile-address').value.trim();
    if (!first_name || !last_name) return showToast('Name fields cannot be empty.', 'error');
    try {
        const updated = await ApiClient.updateProfile({ first_name, last_name, phone_number, address });
        localStorage.setItem('ssp_user', JSON.stringify(updated));
        $('#user-name').textContent = `${updated.first_name} ${updated.last_name}`;
        $('#profile-phone').value = updated.phone_number || '';
        $('#profile-address').value = updated.address || '';
        $('#edit-profile-modal').classList.add('hidden');
        showToast('Profile updated!');
    } catch (err) {
        showToast(err.data?.detail || 'Failed to update profile.', 'error');
    }
});

// ---- Dashboard ----
function initDashboard() {
    const user = ApiClient.getUser();
    if (!user) return switchScreen('login');
    currentRole = user.role;
    $('#user-name').textContent = `${user.first_name} ${user.last_name}`;
    $('#user-role').textContent = user.role;
    switchScreen('dashboard');

    // Role visibility
    $$('.teacher-only').forEach(el => el.classList.toggle('hidden', currentRole !== 'TEACHER'));
    $('#btn-create-class').classList.toggle('hidden', currentRole !== 'TEACHER');

    if (currentRole === 'STUDENT') {
        $('#student-grades-section').classList.remove('hidden');
        fetchStudentGrades();
    } else {
        $('#student-grades-section').classList.add('hidden');
    }
    fetchDashboardClasses();
}

async function fetchStudentGrades() {
    try {
        const grades = await ApiClient.getMyGrades();
        // Group by quiz title
        const grouped = {};
        grades.forEach(g => {
            if (!grouped[g.quiz]) grouped[g.quiz] = { correct: 0, total: 0 };
            grouped[g.quiz].total++;
            if (g.is_correct) grouped[g.quiz].correct++;
        });
        const keys = Object.keys(grouped);
        $('#grades-tbody').innerHTML = keys.length ? keys.map(q => `
            <tr>
                <td><strong>${q}</strong></td>
                <td><span class="badge badge-correct">${grouped[q].correct}</span></td>
                <td>${grouped[q].total}</td>
            </tr>
        `).join('') : '<tr><td colspan="3" class="text-center">No grades yet.</td></tr>';
    } catch (_) {}
}

async function fetchDashboardClasses() {
    const grid = $('#classes-grid');
    grid.innerHTML = '<div class="empty-state"><div class="empty-icon">⏳</div><p>Loading workspaces...</p></div>';
    try {
        const classes = await ApiClient.getClasses();
        if (!classes.length) {
            grid.innerHTML = `<div class="empty-state"><div class="empty-icon">📚</div><p>${currentRole === 'TEACHER' ? 'Create your first workspace to get started.' : 'No classes yet. Ask your teacher to enrol you.'}</p></div>`;
            return;
        }
        grid.innerHTML = classes.map(c => `
            <div class="card class-card" onclick="openClassroom(${c.id}, '${c.name.replace(/'/g, "\\'")}')">
                <div class="class-card-header">
                    <h3>${c.name}</h3>
                    ${currentRole === 'TEACHER' ? `<button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteClass(${c.id})">Delete</button>` : ''}
                </div>
                <div class="card-meta">ID: ${c.id}</div>
            </div>
        `).join('');
    } catch (_) {
        grid.innerHTML = '<div class="empty-state"><div class="empty-icon">⚠️</div><p>Failed to load workspaces.</p></div>';
    }
}

// Create/Delete Class
const classModal = $('#create-class-modal');
$('#btn-create-class').addEventListener('click', () => classModal.classList.remove('hidden'));
$('#btn-cancel-create').addEventListener('click', () => classModal.classList.add('hidden'));
$('#create-class-form').addEventListener('submit', async e => {
    e.preventDefault();
    try {
        await ApiClient.createClass($('#class-name-input').value);
        showToast('Workspace created!');
        classModal.classList.add('hidden');
        $('#class-name-input').value = '';
        fetchDashboardClasses();
    } catch (_) { showToast('Failed to create.', 'error'); }
});

async function deleteClass(id) {
    if (!confirm('Permanently delete this workspace?')) return;
    try { await ApiClient.deleteClass(id); fetchDashboardClasses(); } catch (_) {}
}

// ---- Classroom View ----
$('#btn-back-dash').addEventListener('click', () => {
    if (ws) ws.close();
    activeClassId = null;
    initDashboard();
});

async function openClassroom(id, name) {
    activeClassId = id;
    $('#active-class-title').textContent = name;
    switchScreen('classView');

    // Role controls
    $('#teacher-controls').classList.toggle('hidden', currentRole !== 'TEACHER');
    $('#student-controls').classList.toggle('hidden', currentRole === 'TEACHER');
    $('#btn-clear-hands').classList.toggle('hidden', currentRole !== 'TEACHER');
    $('#enrol-form').classList.toggle('hidden', currentRole !== 'TEACHER');
    $$('.teacher-only').forEach(el => el.classList.toggle('hidden', currentRole !== 'TEACHER'));

    // Reset to feed tab
    $$('.tab').forEach(t => t.classList.remove('active'));
    $$('.tab-content').forEach(c => c.classList.remove('active'));
    $('.tab[data-target="tab-feed"]').classList.add('active');
    $('#tab-feed').classList.add('active');

    refreshActiveTab();
    fetchHands();
    connectWebSocket(id);
}

// ---- Feed / Announcements ----
async function fetchAnnouncements() {
    try {
        const anns = await ApiClient.getAnnouncements(activeClassId);
        $('#announcement-feed').innerHTML = anns.length ? anns.map(a => `
            <div class="feed-item">
                <div class="feed-message">${a.message}</div>
                <div class="feed-time">${fmtDate(a.sent_at)}</div>
            </div>
        `).join('') : '<div class="empty-state"><div class="empty-icon">📢</div><p>No announcements yet.</p></div>';
    } catch (_) {}
}

// Announcement modal
const annModal = $('#announce-modal');
$('#btn-announce').addEventListener('click', () => annModal.classList.remove('hidden'));
$('#btn-cancel-announce').addEventListener('click', () => annModal.classList.add('hidden'));
$('#announce-form').addEventListener('submit', async e => {
    e.preventDefault();
    const msg = $('#announce-message').value.trim();
    if (!msg) return;
    try {
        await ApiClient.createAnnouncement(activeClassId, msg);
        showToast('Announcement posted!');
        annModal.classList.add('hidden');
        $('#announce-message').value = '';
        refreshActiveTab();
    } catch (_) { showToast('Failed.', 'error'); }
});

// ---- Hand Raises ----
async function fetchHands() {
    if (currentRole !== 'TEACHER') return;
    try {
        const hands = await ApiClient.getHandRaises(activeClassId);
        renderHands(hands);
    } catch (_) {}
}

function renderHands(hands) {
    $('#queue-count').textContent = hands.length;
    const list = $('#hand-raise-list');
    if (!hands.length) {
        list.innerHTML = '<div class="empty-state" style="padding:1rem 0"><p>No hands raised.</p></div>';
        return;
    }
    list.innerHTML = hands.map(h => `
        <div class="hand-item">
            <span class="hand-name">🤚 ${h.student_name}</span>
            <div style="display:flex;align-items:center;gap:0.5rem">
                <span class="hand-time">${fmtTime(h.raised_at)}</span>
                ${currentRole === 'TEACHER' ? `<button class="btn btn-sm btn-ghost" onclick="lowerHand(${h.id})" title="Lower">✕</button>` : ''}
            </div>
        </div>
    `).join('');
}

$('#btn-raise-hand').addEventListener('click', async () => {
    try { await ApiClient.raiseHand(activeClassId); showToast('Hand raised!'); } catch (_) { showToast('Already raised.', 'error'); }
});

$('#btn-clear-hands').addEventListener('click', async () => {
    try { await ApiClient.clearHandRaises(activeClassId); showToast('Queue cleared.', 'info'); fetchHands(); } catch (_) {}
});

async function lowerHand(id) {
    try { await ApiClient.lowerHand(id); fetchHands(); } catch (_) {}
}

// ---- Roster ----
async function fetchRoster() {
    try {
        const envs = await ApiClient.getStudents(activeClassId);
        $('#roster-tbody').innerHTML = envs.length ? envs.map(e => `
            <tr>
                <td><strong>${e.student.first_name} ${e.student.last_name}</strong></td>
                <td>${e.student.email}</td>
                ${currentRole === 'TEACHER' ? `<td><button class="btn btn-sm btn-danger" onclick="removeStudent(${e.student.id})">Remove</button></td>` : ''}
            </tr>
        `).join('') : '<tr><td colspan="3" class="text-center">No students enrolled.</td></tr>';
    } catch (_) {}
}

$('#enrol-form').addEventListener('submit', async e => {
    e.preventDefault();
    try {
        await ApiClient.enrolStudent(activeClassId, $('#enrol-email').value);
        showToast('Student enrolled!');
        $('#enrol-email').value = '';
        fetchRoster();
    } catch (err) { showToast(err.data?.detail || 'Failed to enrol.', 'error'); }
});

async function removeStudent(studentId) {
    if (!confirm('Remove this student?')) return;
    try { await ApiClient.removeStudent(activeClassId, studentId); fetchRoster(); } catch (_) {}
}

// ---- Quizzes ----
async function fetchQuizzes() {
    try {
        const quizzes = await ApiClient.getQuizzes(activeClassId);
        const tbody = $('#quizzes-tbody');
        if (!quizzes.length) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No quizzes yet.</td></tr>';
            return;
        }
        tbody.innerHTML = quizzes.map(q => {
            const qCount = q.questions ? q.questions.length : 0;
            let actions = '';
            if (currentRole === 'TEACHER') {
                if (q.status === 'DRAFT') actions = `<button class="btn btn-sm btn-success" onclick="launchQuiz(${q.id})">▶ Launch</button>`;
                else if (q.status === 'LIVE') actions = `<button class="btn btn-sm btn-secondary" onclick="revealQuiz(${q.id})">⏹ End & Reveal</button>`;
                else actions = `<button class="btn btn-sm btn-secondary" onclick="viewResults(${q.id})">📊 Results</button>`;
            } else {
                if (q.status === 'LIVE') actions = `<button class="btn btn-sm btn-primary" onclick="takeQuiz(${q.id})">✏️ Take Quiz</button>`;
                else if (q.status === 'COMPLETED') actions = `<button class="btn btn-sm btn-secondary" onclick="viewResults(${q.id})">📊 My Results</button>`;
                else actions = '<span style="color:var(--text-muted)">Not yet live</span>';
            }
            return `<tr>
                <td><strong>${q.title}</strong></td>
                <td>${qCount}</td>
                <td>${statusBadge(q.status)}</td>
                <td>${actions}</td>
            </tr>`;
        }).join('');
    } catch (_) {
        $('#quizzes-tbody').innerHTML = '<tr><td colspan="4" class="text-center">Failed to load.</td></tr>';
    }
}

// Quiz create modal
const quizModal = $('#create-quiz-modal');
$('#btn-new-quiz').addEventListener('click', () => { $('#quiz-questions-container').innerHTML = ''; addQuestionField(); quizModal.classList.remove('hidden'); });
$('#btn-cancel-quiz').addEventListener('click', () => quizModal.classList.add('hidden'));
$('#btn-add-question').addEventListener('click', addQuestionField);

function addQuestionField() {
    const container = $('#quiz-questions-container');
    const idx = container.children.length;
    const div = document.createElement('div');
    div.className = 'question-builder';
    div.style.cssText = 'background:var(--bg-elevated);border:1px solid var(--border-color);border-radius:var(--radius);padding:1rem;margin-bottom:0.75rem;';
    div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
            <small>Question ${idx + 1}</small>
            ${idx > 0 ? `<button type="button" class="btn btn-sm btn-ghost" onclick="this.closest('.question-builder').remove()" style="color:var(--danger)">✕</button>` : ''}
        </div>
        <input type="text" class="q-text" placeholder="Question text" required style="margin-bottom:0.5rem">
        <input type="text" class="q-options" placeholder="Options (comma separated)" required style="margin-bottom:0.5rem">
        <input type="number" class="q-correct" placeholder="Correct index (0-based)" required min="0" style="margin-bottom:0">
    `;
    container.appendChild(div);
}

$('#create-quiz-form').addEventListener('submit', async e => {
    e.preventDefault();
    const questions = [];
    $$('.question-builder').forEach(qb => {
        const text = qb.querySelector('.q-text').value;
        const options = qb.querySelector('.q-options').value.split(',').map(o => o.trim()).filter(Boolean);
        const correct_index = parseInt(qb.querySelector('.q-correct').value);
        if (text && options.length >= 2) questions.push({ text, options, correct_index });
    });
    if (!questions.length) return showToast('Add at least one question.', 'error');
    try {
        await ApiClient.createQuiz({ class_id: activeClassId, title: $('#quiz-title-input').value, questions });
        showToast('Quiz created!');
        quizModal.classList.add('hidden');
        $('#quiz-title-input').value = '';
        fetchQuizzes();
    } catch (_) { showToast('Failed.', 'error'); }
});

async function launchQuiz(id) {
    try { await ApiClient.launchQuiz(id); showToast('Quiz is LIVE!'); fetchQuizzes(); } catch (_) { showToast('Failed.', 'error'); }
}

async function revealQuiz(id) {
    try { await ApiClient.revealQuiz(id); showToast('Quiz completed & revealed.'); fetchQuizzes(); } catch (_) { showToast('Failed.', 'error'); }
}

// ---- Take Quiz (Student) ----
async function takeQuiz(quizId) {
    const quizzes = await ApiClient.getQuizzes(activeClassId);
    const quiz = quizzes.find(q => q.id === quizId);
    if (!quiz || !quiz.questions.length) return showToast('No questions found.', 'error');

    const panel = $('#quiz-take-panel');
    panel.classList.remove('hidden');
    panel.innerHTML = `
        <h4>📝 ${quiz.title}</h4>
        <div id="quiz-questions-live">
            ${quiz.questions.map((q, qi) => `
                <div class="question-block" id="qblock-${q.id}">
                    <div class="question-text">${qi + 1}. ${q.text}</div>
                    <div class="option-group">
                        ${q.options.map((opt, oi) => `
                            <button type="button" class="option-btn" data-quiz="${quizId}" data-question="${q.id}" data-index="${oi}" onclick="submitOption(this)">${opt}</button>
                        `).join('')}
                    </div>
                    <div class="submit-feedback" id="feedback-${q.id}" style="margin-top:0.5rem;font-size:0.85rem"></div>
                </div>
            `).join('')}
        </div>
        <button class="btn btn-secondary mt-md" onclick="$('#quiz-take-panel').classList.add('hidden')">Close</button>
    `;
}

async function submitOption(btn) {
    const quizId = btn.dataset.quiz;
    const questionId = btn.dataset.question;
    const index = parseInt(btn.dataset.index);

    // Disable all options for this question
    const block = $(`#qblock-${questionId}`);
    block.querySelectorAll('.option-btn').forEach(b => { b.disabled = true; b.classList.remove('selected'); });
    btn.classList.add('selected');

    try {
        const res = await ApiClient.submitAnswer(quizId, questionId, index);
        const fb = $(`#feedback-${questionId}`);
        if (res.is_correct) {
            btn.classList.add('correct');
            fb.innerHTML = '<span class="badge badge-correct">✓ Correct!</span>';
        } else {
            btn.classList.add('wrong');
            fb.innerHTML = '<span class="badge badge-wrong">✕ Incorrect</span>';
        }
    } catch (_) { showToast('Failed to submit.', 'error'); }
}

// ---- View Results ----
async function viewResults(quizId) {
    try {
        const results = await ApiClient.getQuizResults(quizId);
        const panel = $('#quiz-take-panel');
        panel.classList.remove('hidden');

        if (currentRole === 'TEACHER') {
            // Group by student
            const byStudent = {};
            results.forEach(r => {
                if (!byStudent[r.student]) byStudent[r.student] = { correct: 0, total: 0 };
                byStudent[r.student].total++;
                if (r.is_correct) byStudent[r.student].correct++;
            });
            const entries = Object.entries(byStudent);
            panel.innerHTML = `
                <h4>📊 Quiz Results</h4>
                <table>
                    <thead><tr><th>Student</th><th>Score</th><th>Total</th></tr></thead>
                    <tbody>${entries.length ? entries.map(([email, d]) => `
                        <tr><td>${email}</td><td><span class="badge badge-correct">${d.correct}</span></td><td>${d.total}</td></tr>
                    `).join('') : '<tr><td colspan="3" class="text-center">No submissions.</td></tr>'}</tbody>
                </table>
                <button class="btn btn-secondary mt-md" onclick="$('#quiz-take-panel').classList.add('hidden')">Close</button>
            `;
        } else {
            const correct = results.filter(r => r.is_correct).length;
            panel.innerHTML = `
                <h4>📊 Your Results</h4>
                <p style="margin:1rem 0">Score: <span class="badge badge-correct">${correct}</span> / ${results.length}</p>
                <table>
                    <thead><tr><th>Question</th><th>Result</th></tr></thead>
                    <tbody>${results.map(r => `
                        <tr><td>Q${r.question_id}</td><td>${r.is_correct ? '<span class="badge badge-correct">✓ Correct</span>' : '<span class="badge badge-wrong">✕ Wrong</span>'}</td></tr>
                    `).join('')}</tbody>
                </table>
                <button class="btn btn-secondary mt-md" onclick="$('#quiz-take-panel').classList.add('hidden')">Close</button>
            `;
        }
    } catch (_) { showToast('Failed to load results.', 'error'); }
}

// ---- Calendar ----
async function fetchCalendar() {
    try {
        const evs = await ApiClient.getEvents(activeClassId);
        $('#calendar-tbody').innerHTML = evs.length ? evs.map(e => `
            <tr>
                <td><strong>${e.title}</strong></td>
                <td>${fmtDate(e.event_date)}</td>
                ${currentRole === 'TEACHER' ? `<td><button class="btn btn-sm btn-danger" onclick="deleteEvent(${e.id})">Delete</button></td>` : ''}
            </tr>
        `).join('') : '<tr><td colspan="3" class="text-center">No events scheduled.</td></tr>';
    } catch (_) {}
}

const evtModal = $('#create-event-modal');
$('#btn-new-event').addEventListener('click', () => evtModal.classList.remove('hidden'));
$('#btn-cancel-event').addEventListener('click', () => evtModal.classList.add('hidden'));
$('#create-event-form').addEventListener('submit', async e => {
    e.preventDefault();
    try {
        await ApiClient.createEvent(activeClassId, $('#event-title-input').value, $('#event-date-input').value);
        showToast('Event scheduled!');
        evtModal.classList.add('hidden');
        $('#event-title-input').value = '';
        $('#event-date-input').value = '';
        fetchCalendar();
    } catch (_) { showToast('Failed.', 'error'); }
});

async function deleteEvent(id) {
    if (!confirm('Delete this event?')) return;
    try { await ApiClient.deleteEvent(id); fetchCalendar(); } catch (_) {}
}

// ---- Randomizer Tools ----
$('#btn-rand-student').addEventListener('click', async () => {
    try {
        const res = await ApiClient.pickRandomStudent(activeClassId);
        showRandomResult('🎯 Random Pick', `<div style="font-size:1.5rem;font-weight:700;margin:1rem 0">${res.student.name}</div>`);
    } catch (_) { showToast('No students to pick.', 'error'); }
});

$('#btn-generate-groups').addEventListener('click', async () => {
    const size = parseInt(prompt('Group size:', '2'));
    if (!size || size < 1) return;
    try {
        const res = await ApiClient.generateGroups(activeClassId, size);
        const html = res.groups.map((g, i) => `<div class="result-card"><strong>Group ${i + 1}</strong><br>${g.map(s => s.name).join(', ')}</div>`).join('');
        showRandomResult('👥 Random Groups', `<div class="result-grid">${html}</div>`);
    } catch (_) { showToast('Failed.', 'error'); }
});

$('#btn-presentation-order').addEventListener('click', async () => {
    try {
        const res = await ApiClient.getPresentationOrder(activeClassId);
        const html = res.order.map((s, i) => `<div class="result-card">${i + 1}. ${s.name}</div>`).join('');
        showRandomResult('📋 Presentation Order', `<div class="result-grid">${html}</div>`);
    } catch (_) { showToast('Failed.', 'error'); }
});

function showRandomResult(title, content) {
    const modal = $('#random-result-modal');
    $('#random-result-title').textContent = title;
    $('#random-result-body').innerHTML = content;
    modal.classList.remove('hidden');
}
$('#btn-close-random').addEventListener('click', () => $('#random-result-modal').classList.add('hidden'));

// ---- WebSocket ----
function connectWebSocket(classId) {
    if (ws) ws.close();
    ws = new WebSocket(`ws://127.0.0.1:8000/ws/classroom/${classId}/`);
    const ind = $('#ws-indicator');

    ws.onopen = () => { ind.style.background = 'var(--success)'; ind.textContent = 'Live'; };
    ws.onclose = () => { ind.style.background = 'var(--danger)'; ind.textContent = 'Offline'; };

    ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        const evt = msg.event;
        if (evt === 'hand_raised' || evt === 'hand_lowered' || evt === 'queue_cleared') fetchHands();
        if (evt === 'new_announcement') {
            showToast('📢 New announcement!', 'info');
            if ($('.tab-content.active')?.id === 'tab-feed') fetchAnnouncements();
        }
        if (evt === 'quiz_launched') {
            showToast('🚀 A quiz is now LIVE!', 'info');
            if ($('.tab-content.active')?.id === 'tab-quizzes') fetchQuizzes();
        }
        if (evt === 'quiz_completed') {
            showToast('Quiz ended — results available.', 'info');
            if ($('.tab-content.active')?.id === 'tab-quizzes') fetchQuizzes();
        }
    };
}

// ---- Bootstrap ----
if (ApiClient.getUser() && ApiClient.getToken()) {
    initDashboard();
} else {
    switchScreen('login');
}
