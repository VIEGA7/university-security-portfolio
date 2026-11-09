let token;
let role;
const status = document.getElementById('status');
async function csrf() {
    const response = await fetch('/api/csrf');
    if (!response.ok) throw new Error(`CSRF: ${response.status}`);
    token = (await response.json()).token;
}
async function request(path, method = 'GET', data) {
    const response = await fetch(path, {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': token || '' },
        body: data === undefined ? undefined : JSON.stringify(data)
    });
    if (!response.ok) throw new Error(`Запрос отклонён: ${response.status}`);
    return response.status === 204 ? null : response.json();
}
function message(error) { status.textContent = error.message; }
async function show() {
    const users = await request('/api/users');
    const list = document.getElementById('users');
    list.replaceChildren();
    for (const user of users) {
        const item = document.createElement('li');
        item.textContent = `${user.name}, ${user.age} лет `;
        if (role === 'admin') {
            const button = document.createElement('button');
            button.textContent = 'Удалить';
            button.onclick = async () => {
                try { await request(`/api/users/${user.id}`, 'DELETE'); await show(); }
                catch (error) { message(error); }
            };
            item.append(button);
        }
        list.append(item);
    }
}
async function signedIn(me) {
    role = me.role;
    await csrf(); // Antiforgery tokens are bound to the authenticated identity.
    document.getElementById('login').hidden = true;
    document.getElementById('workspace').hidden = false;
    document.getElementById('create').hidden = role !== 'admin';
    status.textContent = `${me.username} (${role})`;
    await show();
}
document.getElementById('login').onsubmit = async event => {
    event.preventDefault();
    try {
        await csrf();
        const me = await request('/api/login', 'POST', {
            username: document.getElementById('username').value,
            password: document.getElementById('password').value
        });
        document.getElementById('password').value = '';
        await signedIn(me);
    } catch (error) { message(error); }
};
document.getElementById('create').onsubmit = async event => {
    event.preventDefault();
    try {
        await request('/api/users', 'POST', {
            name: document.getElementById('name').value,
            age: Number(document.getElementById('age').value)
        });
        event.target.reset();
        await show();
    } catch (error) { message(error); }
};
document.getElementById('refresh').onclick = () => show().catch(message);
document.getElementById('logout').onclick = async () => {
    try {
        await request('/api/logout', 'POST');
        document.getElementById('workspace').hidden = true;
        document.getElementById('login').hidden = false;
        document.getElementById('users').replaceChildren();
        status.textContent = 'Вы вышли';
        role = null;
        await csrf();
    } catch (error) { message(error); }
};
(async () => {
    await csrf();
    const response = await fetch('/api/me');
    if (response.ok) await signedIn(await response.json());
})().catch(message);
