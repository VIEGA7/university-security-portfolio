// Partial reconstruction from practice 7: alert and XMLHttpRequest + JSON sum.
document.getElementById('alert').onclick = () => alert('JavaScript is magic!');
document.getElementById('sum').onclick = () => {
    const xhr = new XMLHttpRequest();
    const output = document.getElementById('result');
    xhr.open('GET', '/array.json');
    xhr.timeout = 5000;
    xhr.onload = () => {
        try {
            if (xhr.status !== 200) throw new Error(`HTTP ${xhr.status}`);
            const data = JSON.parse(xhr.responseText);
            if (!Array.isArray(data.summe) || !data.summe.every(Number.isFinite))
                throw new Error('Ожидался массив чисел summe');
            output.textContent = `Сумма: ${data.summe.reduce((sum, n) => sum + n, 0)}`;
        } catch (error) { output.textContent = error.message; }
    };
    xhr.onerror = () => { output.textContent = 'Ошибка сети'; };
    xhr.ontimeout = () => { output.textContent = 'Время ожидания истекло'; };
    xhr.send();
};
