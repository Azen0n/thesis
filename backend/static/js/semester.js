document.addEventListener('DOMContentLoaded', main, false);

function main() {
    addGenerateCodeFormListener();
    addJoinCodeFormListener();
    addChangeTargetPointsListener();
}

function addJoinCodeFormListener() {
    let joinCodeForm = document.getElementById('join_code_form');
    if (joinCodeForm != null) {
        joinCodeForm.addEventListener(
            'submit', function (e) {
                enroll().then((data) => {
                        let result = JSON.parse(data);
                        if (result['error'] !== undefined) {
                            let errorElement = document.getElementById('error');
                            errorElement.innerText = result['error'];
                        }
                        else if (result['status'] === '200') {
                            window.location.replace(window.location.href);
                        }
                    }
                );
                e.preventDefault();
            }
        );
    }
}

function addGenerateCodeFormListener() {
    let codeForm = document.getElementById('generate_code_form');
    if (codeForm != null) {
        codeForm.addEventListener(
            'submit', function (e) {
                generateSemesterCode().then((data) => {
                        let result = JSON.parse(data);
                        let codeElement = document.getElementById('code');
                        if (!result['is_code_expired']) {
                            codeElement.innerText = `Код для присоединения: ${result['code']}`;
                        }
                        else {
                            codeElement.innerText = `Срок действия кода истек.`;
                        }
                    }
                );
                e.preventDefault();
            }
        );
    }
}

async function generateSemesterCode() {
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let response = await fetch('generate_semester_code/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({'expiration_time': document.getElementById('expiration_date').value})
    });
    return response.json();
}

async function enroll() {
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let response = await fetch('enroll/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({'code': document.getElementById('join_code').value})
    });
    return response.json();
}

function addChangeTargetPointsListener() {
    document.getElementById('target_points_form').addEventListener('submit', function (e) {
        changeTargetPoints().then(response => {});
        e.preventDefault();
    });
}

async function changeTargetPoints() {
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let response = await fetch('/change_target_points/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({'points': document.getElementById('target_points').value})
    });
    return response.json();
}
