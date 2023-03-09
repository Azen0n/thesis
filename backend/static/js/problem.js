document.addEventListener('DOMContentLoaded', main, false);

function main() {
    let answerElement = document.getElementById('answer');
    renderAnswer(answerElement);
    let resultElement = document.getElementById('result');

    document.getElementById('answer_form').addEventListener('submit', function (e) {
        validateAnswer(answerElement).then((data) => {
            let result = JSON.parse(data);
            console.log(result);
            let coefficient = result['coefficient'];
            if (coefficient === undefined) {
                coefficient = result['error'];
            } else {
                let submitButton = document.getElementById('submit_button');
                submitButton.remove();
            }
            resultElement.innerHTML = `${coefficient}`;
        });
        e.preventDefault();
    })
}

function renderAnswer(answerElement) {
    let answer = JSON.parse(answerElement.dataset.answer);
    let correctAnswers = JSON.parse(answerElement.dataset.correct);
    switch (answer['type']) {
        case 'Multiple Choice Radio':
            multipleChoiceRadio(answer, answerElement, correctAnswers);
            break;
        case 'Multiple Choice Checkbox':
            multipleChoiceCheckbox(answer, answerElement, correctAnswers);
            break;
        case 'Fill In Single Blank':
            fillInSingleBlank(answerElement, correctAnswers);
            break;
        default:
            console.error(`Unknown type '${answer['type']}'`);
    }
}

function multipleChoiceRadio(answer, answerElement, correctAnswers) {
    let options = [];
    for (let option of answer['options']) {
        if (correctAnswers == null) {
            options.push(`
            <input type="radio" id="${option['id']}" value="${option['text']}" name="option">
            <label for="${option['id']}">${option['text']}</label><br>
        `);
        } else {
            let checked = option['id'] === correctAnswers['is_correct'] ? ' checked' : '';
            options.push(`
            <input type="radio" id="${option['id']}" value="${option['text']}" name="option"${checked} disabled>
            <label for="${option['id']}">${option['text']}</label><br>
        `);
        }
    }
    answerElement.innerHTML = `
        <fieldset>
            <legend>Выберите один правильный вариант</legend>
            ${options.join('\n')}
        </fieldset>
    `;
}

function multipleChoiceCheckbox(answer, answerElement, correctAnswers) {
    let options = [];
    for (let option of answer['options']) {
        if (correctAnswers == null) {
            options.push(`
            <input type="checkbox" id="${option['id']}" value="${option['text']}" name="option">
            <label for="${option['id']}">${option['text']}</label><br>
        `);
        } else {
            let checked = correctAnswers['is_correct'].includes(option['id']) ? ' checked' : '';
            options.push(`
            <input type="checkbox" id="${option['id']}" value="${option['text']}" name="option"${checked} disabled>
            <label for="${option['id']}">${option['text']}</label><br>
        `);
        }
    }
    answerElement.innerHTML = `
        <fieldset>
            <legend>Выберите несколько правильных вариантов</legend>
            ${options.join('\n')}
        </fieldset>
    `;
}

function fillInSingleBlank(answerElement, correctAnswers) {
    if (correctAnswers == null) {
        answerElement.innerHTML = `
        <p>Введите ответ</p>
        <input type="text"></span>
    `;
    } else {
        answerElement.innerHTML = `
        <p>Введите ответ</p>
        <input type="text" value="${correctAnswers['is_correct'].join(', ')}" disabled></span>
    `;
    }
}

function getAnswerData() {
    let answerElement = document.getElementById('answer');
    let answerType = JSON.parse(answerElement.dataset.answer)['type'];
    let data;
    switch (answerType) {
        case 'Multiple Choice Radio':
            data = getMultipleChoiceRadioAnswer(answerElement);
            data['type'] = 'Multiple Choice Radio';
            break;
        case 'Multiple Choice Checkbox':
            data = getMultipleChoiceCheckboxAnswer(answerElement);
            data['type'] = 'Multiple Choice Checkbox';
            break;
        case 'Fill In Single Blank':
            data = getFillInSingleBlankAnswer(answerElement);
            data['type'] = 'Fill In Single Blank';
            break;
        default:
            console.error(`Unknown type '${answerType}'`);
    }
    return data;
}

function getMultipleChoiceRadioAnswer(answerElement) {
    let inputs = answerElement.querySelectorAll('input');
    let answer = {'answer_id': undefined};
    for (let input of inputs) {
        if (input.checked) {
            answer['answer_id'] = input.id;
            break;
        }
    }
    return answer;
}

function getMultipleChoiceCheckboxAnswer(answerElement) {
    let inputs = answerElement.querySelectorAll('input');
    let answer = {'answer_id': []};
    for (let input of inputs) {
        if (input.checked) {
            answer['answer_id'].push(input.id);
        }
    }
    return answer;
}

function getFillInSingleBlankAnswer(answerElement) {
    let input = answerElement.querySelectorAll('input')[0];
    return {'value': input.value, 'problem_id': answerElement.parentElement.parentElement.dataset.problem};
}

async function validateAnswer(answerElement) {
    const problemElement = answerElement.parentElement.parentElement;
    const url = `/semesters/${problemElement.dataset.semester}/problems/${problemElement.dataset.problem}/validate_answer/`;
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify(getAnswerData())
    });
    return response.json();
}