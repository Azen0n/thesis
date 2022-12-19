document.addEventListener('DOMContentLoaded', main, false);

function main() {
    let answerElement = document.getElementById('answer');
    let answer = JSON.parse(answerElement.dataset.answer);

    switch (answer['type']) {
        case 'Multiple Choice Radio':
            multipleChoiceRadio(answer, answerElement);
            break;
        case 'Multiple Choice Checkbox':
            multipleChoiceCheckbox(answer, answerElement);
            break;
        case 'Fill In Single Blank':
            fillInSingleBlank(answer, answerElement);
            break;
        default:
            console.error(`Unknown type '${answer['type']}'`);
    }
}

function multipleChoiceRadio(answer, answerElement) {
    let options = [];
    for (let option of answer['options']) {
        options.push(`
            <input type="radio" id="${option['id']}" value="${option['text']}" name="option">
            <label for="${option['id']}">${option['text']}</label><br>
        `);
    }
    answerElement.innerHTML = `
        <fieldset>
            <legend>Выберите один правильный вариант</legend>
            ${options.join('\n')}
        </fieldset>
    `;
}

function multipleChoiceCheckbox(answer, answerElement) {
    let options = [];
    for (let option of answer['options']) {
        options.push(`
            <input type="checkbox" id="${option['id']}" value="${option['text']}" name="option">
            <label for="${option['id']}">${option['text']}</label><br>
        `);
    }
    answerElement.innerHTML = `
        <fieldset>
            <legend>Выберите несколько правильных вариантов</legend>
            ${options.join('\n')}
        </fieldset>
    `;
}

function fillInSingleBlank(answer, answerElement) {
    let optionText = answer['options']['text'];
    optionText = optionText.split('{}');
    answerElement.innerHTML = `
        <p>Заполните пропуск</p>
        <p>${optionText[0]}<span><input type="text"></span>${optionText[1]}</p>
    `;
}