/* ============================================================
   Smart Study Portal — API Client
   Handles all HTTP communication with the Django backend.
   ============================================================ */

const API_BASE = "http://127.0.0.1:8000";

const ApiClient = {
    /* ---- Token helpers ---- */
    getToken() { return localStorage.getItem('ssp_token'); },
    setToken(t) { localStorage.setItem('ssp_token', t); },
    clearAuth() { localStorage.removeItem('ssp_token'); localStorage.removeItem('ssp_user'); },
    getUser() { const u = localStorage.getItem('ssp_user'); return u ? JSON.parse(u) : null; },

    /* ---- Core request handler ---- */
    async request(endpoint, method = 'GET', body = null) {
        const headers = { 'Content-Type': 'application/json' };

        // Skip auth header on public auth routes to avoid stale-token rejections
        if (!endpoint.startsWith('/auth/')) {
            const token = this.getToken();
            if (token) headers['Authorization'] = `Bearer ${token}`;
        }

        // Only send cookies on endpoints that set/read the refresh_token cookie
        const needsCookies = endpoint === '/auth/login/' || endpoint === '/auth/refresh/';
        const config = { method, headers, credentials: needsCookies ? 'include' : 'omit' };
        if (body) config.body = JSON.stringify(body);

        const res = await fetch(`${API_BASE}${endpoint}`, config);
        const isJson = res.headers.get('content-type')?.includes('application/json');
        const data = isJson ? await res.json() : null;

        if (!res.ok) {
            if (res.status === 401 && !endpoint.startsWith('/auth/login')) {
                this.clearAuth();
                window.dispatchEvent(new Event('auth_expired'));
            }
            throw { status: res.status, data };
        }
        return data;
    },

    /* ---- Auth ---- */
    login(email, password)  { return this.request('/auth/login/', 'POST', { email, password }); },
    logout()                { return this.request('/auth/logout/', 'POST'); },
    getMe()                 { return this.request('/me/'); },
    updateProfile(data)      { return this.request('/me/', 'PATCH', data); },
    resetPasswordRequest(email)                    { return this.request('/auth/password-reset/request/', 'POST', { email }); },
    resetPasswordConfirm(uid, token, new_password) { return this.request('/auth/password-reset/confirm/', 'POST', { uid, token, new_password }); },

    /* ---- Classes ---- */
    getClasses()            { return this.request('/classes/'); },
    createClass(name)       { return this.request('/classes/', 'POST', { name }); },
    getClassDetail(id)      { return this.request(`/classes/${id}/`); },
    updateClass(id, data)   { return this.request(`/classes/${id}/`, 'PATCH', data); },
    deleteClass(id)         { return this.request(`/classes/${id}/`, 'DELETE'); },

    /* ---- Enrolments ---- */
    getStudents(classId)                  { return this.request(`/classes/${classId}/students/`); },
    enrolStudent(classId, email)          { return this.request(`/classes/${classId}/students/`, 'POST', { email }); },
    removeStudent(classId, studentId)     { return this.request(`/classes/${classId}/students/${studentId}/`, 'DELETE'); },

    /* ---- Announcements ---- */
    getAnnouncements(classId)             { return this.request(`/classes/${classId}/announcements/`); },
    createAnnouncement(classId, message)  { return this.request(`/classes/${classId}/announcements/`, 'POST', { message }); },

    /* ---- Quizzes ---- */
    getQuizzes(classId)                              { return this.request(`/quizzes/?class_id=${classId}`); },
    createQuiz(body)                                 { return this.request('/quizzes/', 'POST', body); },
    launchQuiz(quizId)                               { return this.request(`/quizzes/${quizId}/launch/`, 'POST'); },
    submitQuiz(quizId, answers)                      { return this.request(`/quizzes/${quizId}/submit/`, 'POST', { answers }); },
    submitAnswer(quizId, questionId, selected_index) { return this.request(`/quizzes/${quizId}/questions/${questionId}/submit/`, 'POST', { selected_index }); },
    revealQuiz(quizId)                               { return this.request(`/quizzes/${quizId}/reveal/`, 'POST'); },
    getQuizResults(quizId)                           { return this.request(`/quizzes/${quizId}/results/`); },
    getMyGrades()                                    { return this.request('/me/grades/'); },

    /* ---- Calendar ---- */
    getEvents(classId)                            { return this.request(`/classes/${classId}/calendar/`); },
    createEvent(classId, title, start_date, end_date) { return this.request(`/classes/${classId}/calendar/`, 'POST', { title, start_date, end_date }); },
    updateEvent(eventId, data)                     { return this.request(`/calendar/${eventId}/`, 'PATCH', data); },
    deleteEvent(eventId)                           { return this.request(`/calendar/${eventId}/`, 'DELETE'); },

    /* ---- Hand Raises ---- */
    getHandRaises(classId)    { return this.request(`/classes/${classId}/hand-raises/`); },
    raiseHand(classId)        { return this.request('/hand-raises/', 'POST', { class_id: classId }); },
    lowerHand(handId)         { return this.request(`/hand-raises/${handId}/`, 'DELETE'); },
    clearHandRaises(classId)  { return this.request(`/classes/${classId}/hand-raises/`, 'DELETE'); },

    /* ---- Randomizers ---- */
    pickRandomStudent(classId)          { return this.request('/random/pick-student/', 'POST', { class_id: classId }); },
    generateGroups(classId, group_size) { return this.request('/random/groups/', 'POST', { class_id: classId, group_size }); },
    getGroups(classId)                  { return this.request(`/classes/${classId}/groups/`); },
    getPresentationOrder(classId)       { return this.request('/random/presentation-order/', 'POST', { class_id: classId }); },
};
