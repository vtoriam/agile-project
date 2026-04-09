let exampleTaskName = "Clean the kitchen";
let exampleTaskPoints = 15;
let exampleSubtasks = ["Unstack and/or stack the dishwasher"
                ,"Wash the dishes"
                ,"Wipe the benches"];

let exampleTaskName2 = "Water the plants";
let exampleTaskPoints2 = 15;
let exampleSubtasks2 = ["Water the grass"
                ,"Water the plants round the side"
                ,"Water up the driveway"];

let subtaskInputs = 0;

function createTask(exampleTaskName, exampleTaskPoints, exampleSubtasks) {
    let task = document.createElement("div");
    task.classList.add("task");

    let mainTask = document.createElement("div");
    mainTask.classList.add("main-task");

    let taskBody = document.createElement("div");
    taskBody.classList.add("task-body", "card");

    let taskName = document.createElement("h2");
    taskName.classList.add("task-name", "card-header");
    taskName.textContent = exampleTaskName;

    let subtaskCollapse = document.createElement("button");
    subtaskCollapse.classList.add("subtask-collapse", "card-footer");
    subtaskCollapse.setAttribute("data-bs-toggle", "collapse");
    subtaskCollapse.setAttribute("aria-expanded", "false");
    subtaskCollapse.textContent = "See subtasks";

    taskBody.appendChild(taskName);
    taskBody.appendChild(subtaskCollapse);

    let taskSide = document.createElement("div");
    taskSide.classList.add("task-side");

    let claim = document.createElement("button");
    claim.classList.add("claim");
    claim.textContent = "Claim";

    let points = document.createElement("div");
    points.classList.add("points", "card");
    points.textContent = exampleTaskPoints + " Pts";

    // let checkboxContainer = document.createElement("div");
    // checkboxContainer.classList.add("checkbox-container");
    let claimedTask = document.createElement("label");
    claimedTask.classList.add("claimed-task");
    claimedTask.innerHTML = "<input type='checkbox'>";

    // let newCheckbox = document.createElement("span");
    // newCheckbox.classList.add("new-checkbox");


    // checkboxContainer.appendChild(claimedTask);
    // checkboxContainer.appendChild(newCheckbox);
    


    taskSide.appendChild(claim);
    taskSide.appendChild(points);

    mainTask.appendChild(taskBody);
    mainTask.appendChild(taskSide);

    let subtasks = document.createElement("div");
    subtasks.classList.add("subtasks", "card","collapse");
    let subtasksId = exampleTaskName.replace(/\s/g, "");
    subtasks.setAttribute("id", subtasksId);
    subtasksId = "#" + subtasksId
    subtaskCollapse.setAttribute("data-bs-target", subtasksId);
    subtaskCollapse.setAttribute("aria-controls", subtasks);
    

    for (let i = 0; i < exampleSubtasks.length; i++) {
        let subtaskCheckbox = document.createElement("input");
        subtaskCheckbox.setAttribute("type", "checkbox");

        let subtaskLabel = document.createElement("label");
        subtaskLabel.appendChild(subtaskCheckbox);
        subtaskDescription = document.createElement("span");
        subtaskDescription.textContent = " " + exampleSubtasks[i]
        subtaskLabel.appendChild(subtaskDescription);

        subtasks.appendChild(subtaskLabel);
        // subtasks.appendChild(document.createElement("br"));
    }

    task.appendChild(mainTask);
    task.appendChild(subtasks);

    document.body.appendChild(task);

    claim.addEventListener("click", () => {
            claim.parentNode.replaceChild(claimedTask, claim);
    });
}

function createSubtask() {
    subtaskInputs += 1;
    let subtaskField = document.createElement("input");
    subtaskField.setAttribute("type", "text");
    let subtaskLabel = document.createElement("label");
    subtaskLabel.textContent = subtaskInputs;
    inputField = document.getElementById("input-field");
    inputField.appendChild(subtaskLabel);
    inputField.appendChild(subtaskField);
    inputField.appendChild(document.createElement("br"));
}

createTask(exampleTaskName, exampleTaskPoints, exampleSubtasks);
createTask(exampleTaskName2, exampleTaskPoints2, exampleSubtasks2);

function removeSubtask() {
    if (subtaskInputs > 0) {
        subtaskInputs -= 1;
        let inputField = document.getElementById("input-field");
        for (let i = 0; i < 3; i++) {
            let lastSubtask = inputField.lastChild
            inputField.removeChild(lastSubtask);
        }
    }
}

addSubtaskButton = document.getElementById("addSubtask");
addSubtaskButton.addEventListener("click", () => {
    createSubtask();
});

removeSubtaskButton = document.getElementById("removeSubtask");
removeSubtaskButton.addEventListener("click", () => {
    removeSubtask();
});

function submitTask() {
    let taskName = document.querySelector("#input-field input").value;
    let taskPoints = document.querySelectorAll("#input-field input")[1].value;
    let subtasks = [];
    for (let i = 2; i < subtaskInputs + 2; i++) {
        subtasks.push(document.querySelectorAll("#input-field input")[i].value);
    }
    createTask(taskName, taskPoints, subtasks);
}

submitTaskButton = document.getElementById("submitTask");
submitTaskButton.addEventListener("click", () => {
    submitTask();
});