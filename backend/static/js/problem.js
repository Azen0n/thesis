document.addEventListener('DOMContentLoaded', main, false);
let instance;
let stopwatchElement;

function main() {
    let descriptionElement = document.getElementById('description');
    descriptionElement.innerHTML = marked.parse(descriptionElement.innerText);

    stopwatchElement = document.getElementById('stopwatch');
    setInterval(updateStopwatch, 1000);

    let answerElement = document.getElementById('answer');
    if (answerElement !== null) {
        renderAnswer(answerElement);

        let resultElement = document.getElementById('result');

        document.getElementById('answer_form').addEventListener('submit', function (e) {
            resultElement.innerHTML = '<span class="iconify" data-icon="eos-icons:three-dots-loading" data-width="30"></span>';
            validateAnswer(answerElement).then((data) => {
                try {
                    processAnswerResultData(data);
                } catch (error) {
                    console.log(error);
                    resultElement.innerHTML = 'Произошла неизвестная ошибка.';
                }
            });
            e.preventDefault();
        });
        let stdinBtn = document.getElementById('run_stdin_button');
        if (stdinBtn !== null) {
            stdinBtn.addEventListener('click', function () {
                resultElement.innerHTML = '<span class="iconify" data-icon="eos-icons:three-dots-loading" data-width="30"></span>';
                runStdin(answerElement).then((data) => {
                    try {
                        processRunStdinResultData(data);
                    } catch (error) {
                        console.log(error);
                        resultElement.innerHTML = 'Произошла неизвестная ошибка.';
                    }
                });
            });
        }
    }
}

function renderAnswer(answerElement) {
    let answer = JSON.parse(answerElement.dataset.answer);
    let correctAnswers = answerElement.dataset.correct;
    if (correctAnswers !== undefined) {
        correctAnswers = JSON.parse(answerElement.dataset.correct);
    }
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
        case 'Code':
            code(answerElement, correctAnswers);
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
        <input type="text">
    `;
    } else {
        answerElement.innerHTML = `
        <p>Введите ответ</p>
        <input type="text" value="${correctAnswers['is_correct'].join(', ')}" disabled>
    `;
    }
}

function code(answerElement, correctAnswers) {
    if (correctAnswers == null) {
        if (document.getElementById('run_stdin_button') !== null) {
            renderCode(answerElement);
        }
    } else {
        let tests = correctAnswers['is_correct'].split('\n');
        answerElement.innerHTML = ``;
        for (let i = 1; i < tests.length; i += 2) {
            let stdin = tests[i - 1].split(',\r').filter(n => n);
            answerElement.innerHTML += createTestElement(i, stdin, tests[i]);
        }
    }
}

function renderCode(answerElement) {
    answerElement.innerHTML = `
        <div class="d-flex justify-content-start align-items-center my-2">
            <div class="bold_text">Код на Python (stdin → stdout)</div>
            <a id="code_info_button" class="d-flex ms-2 align-items-center">
                <span class="iconify" data-icon="material-symbols:info" style="color: #6c757d; cursor: pointer;"
                      data-width="20" data-height="20"></span>
            </a>
        </div>
        <div id="code_info" style="display: none;">
            Особенности запуска кода:
            <ol>
                <li>Если в задании присутствуют входные данные, программа должна считывать их с клавиатуры
                 (например, <span class="code-font">x = float(input())</span>). Каждый параметр во входных данных вводится с новой строки,
                    если иного не указано в задании.</li>
                <li>Если в задании явно не указан тип вводимых параметров, результат <span class="code-font">input</span> приводится к 
                 <span class="code-font">float</span> (например, <span class="code-font">x = float(input())</span>).</li>
                <li>Все математические операции, кроме инкремента, приводятся к <span class="code-font">float</span>.</li>
                <li>Внутри <span class="code-font">input()</span> не должно быть текста. <span class="code-font">print()</span> должен
                 выводить только то, что требуется в задании.</li>
                <li>Управляющие последовательности необходимо экранировать. Например, <span class="code-font">"\\n"</span> →
                 <span class="code-font">"\\\\n"</span>.</li>
            </ol>
        </div>
        <div id="code" style="position: relative; border: 2px solid #ccc; width: 100%;"></div>
    `;
    document.getElementById('code_info_button').addEventListener('click', function () {
        let codeInfo = document.getElementById('code_info');
        if (codeInfo.style.display === 'none') {
            codeInfo.style.display = 'block';
        } else {
            codeInfo.style.display = 'none';
        }
    });
    let codeElement = document.getElementById('code');
    instance = CodeMirror(codeElement, {
        lineNumbers: true,
        mode: 'python',
        indentUnit: 4,
        textHeight: 18,
    });
}

function createTestElement(testNumber, input, output) {
    return `<div class="bold_text">Тест ${testNumber}</div>
                <div class="container">
                    <div class="row justify-content-start">
                        <div class="col-3 px-0">
                            <div class="container ps-0">
                                <label class="bold_text" for="stdin_example${testNumber}">Ввод</label>
                                <div id="stdin_example${testNumber}" class="code-font code-number"
                                     style="width: 100px; height: 30px;">
                                    ${input}
                                </div>
                            </div>
                        </div>
                        <div class="col-3 px-0">
                            <div class="container ps-0">
                                <label class="bold_text" for="stdout_example${testNumber}">Вывод</label>
                                <div id="stdout_example${testNumber}" class="code-font code-number"
                                     style="width: 100px; height: 30px;">
                                    ${output}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>`;
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
        case 'Code':
            data = getCodeAnswer(answerElement);
            data['type'] = 'Code';
            break;
        default:
            console.error(`Unknown type '${answerType}'`);
    }
    data['time_elapsed_in_seconds'] = parseInt(stopwatchElement.innerHTML);
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

function getCodeAnswer(answerElement) {
    return {'code': instance.getValue(), 'problem_id': answerElement.parentElement.parentElement.dataset.problem};
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

async function runStdin(answerElement) {
    const problemElement = answerElement.parentElement.parentElement;
    const url = `/semesters/${problemElement.dataset.semester}/problems/${problemElement.dataset.problem}/run_stdin/`;
    const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value;
    let data = getAnswerData();
    data['stdin'] = document.getElementById('stdin').value;
    let response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify(data)
    });
    return response.json();
}

function processAnswerResultData(data) {
    let result = JSON.parse(data);
    console.log(result);
    let coefficient = result['coefficient'];
    if (coefficient === undefined) {
        coefficient = `<div class="d-flex align-items-center">
            <span class="iconify me-2" data-icon="tabler:info-triangle-filled" style="color: #fbe106;" data-width="20"></span>
            <div>${result['error']}</div>
        </div>`;
    } else {
        coefficient = parseInt(coefficient) === 1 ? 'Верно' : 'Неверно';
        coefficient += ` (${result['answer'][1]})`;
        if (result['is_answered'] === true) {
            removeCodeControls();
        }
    }
    let resultElement = document.getElementById('result');
    resultElement.innerHTML = `${coefficient}`;
}

function processRunStdinResultData(data) {
    let resultElement = document.getElementById('result');
    let result = JSON.parse(data);
    console.log(result);
    if (result['code'] === undefined) {
        if (result['error'] === undefined) {
            resultElement.innerHTML = 'Произошла неизвестная ошибка';
        } else {
            resultElement.innerHTML = `<div class="d-flex align-items-center">
            <span class="iconify me-2" data-icon="tabler:info-triangle-filled" style="color: #fbe106;" data-width="20"></span>
            <div>${result['error']}</div>
        </div>`;
        }
    } else {
        let info = '<br>';
        if (result['stderr'] === '') {
            info += `Вывод:<br><pre><div class="code-font code-number">${encodeHtmlEntities(result['stdout'])}</div></pre>`;
        } else {
            info += `Ошибка:<br><pre><div class="code-font code-number">${encodeHtmlEntities(result['stderr'])}</div></pre>`;
        }
        resultElement.innerHTML = `${result['code']}${info}`;
    }
}

function encodeHtmlEntities(str) {
    const htmlEntities = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&apos;',
        '/': '&sol;',
        '`': '&grave;',
        '(': '&#40;',
        ')': '&#41;',
        '+': '&#43;',
        '-': '&#45;',
        ';': '&#59;',
        '=': '&#61;',
        '[': '&#91;',
        ']': '&#93;',
        '^': '&#94;',
        '{': '&#123;',
        '|': '&#124;',
        '}': '&#125;',
        '~': '&#126;',
    };
    return str.replace(/[&<>"'/`()+\-;=\[\]^{|}~]/g, function (match) {
        return htmlEntities[match] || match;
    });
}

function updateStopwatch() {
    stopwatchElement.innerHTML = parseInt(stopwatchElement.innerHTML) + 1;
}

function removeCodeControls() {
    document.getElementById('submit_button').remove();
    document.getElementById('run_stdin_button').remove();
    document.getElementById('stdin_label_input').remove();
    document.getElementById('skip_button').remove();
    instance.setOption('readOnly', 'true');
}
