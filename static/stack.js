function nextPage(pageNumber) {
  window.location.href = "deployment";
}

async function showToast(message, toasterId) {
  var toasterElement = document.getElementById(toasterId);
  toasterElement.querySelector(".toast-body").textContent = message;
  var toaster = new bootstrap.Toast(toasterElement);
  toaster.show();
  setTimeout(function () {
    toaster.hide();
  }, 5000);
}

async function apicall() {
  const githubUrl = localStorage.getItem("githubUrl");
  const repoName = localStorage.getItem("repoName");
  const repoCloneUrl = localStorage.getItem("repoCloneUrl");
  const repoLanguage = localStorage.getItem("repoLanguage");
  const repoPrivate = localStorage.getItem("repoPrivate");
  const branchName = localStorage.getItem("branchName");
  const port = document.getElementById("port").value;
  const stack = document.getElementById("stack").value;
  try {
    const response = await fetch("/stack", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        github_url: githubUrl,
        reponame: repoName,
        branch: branchName,
        port: port,
        stack: stack,
      }),
    });

    if (!response.ok) {
      document.getElementById("loader").style.display = "none";
      await showToast("Error: Invalid Github URL", "toasterFail");
    } else {
      const data = await response.json();
      localStorage.setItem("port", port);
      localStorage.setItem("stack", stack);
      // document.getElementById("message2").innerHTML =
      //   "<a href='" + data.github_url + "'>Jenkins Report</a>";
      const nextButton = document.getElementById("nextButton");
      nextButton.style.display = "block";
      await showToast("Success: Valid Github URL", "toasterSuccess");
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader").style.display = "none";
  }
}

async function getRepoDetails() {
  const githubUrl = localStorage.getItem("githubUrl");
  const repoName = localStorage.getItem("repoName");
  const repoCloneUrl = localStorage.getItem("repoCloneUrl");
  const repoLanguage = localStorage.getItem("repoLanguage");
  const repoPrivate = localStorage.getItem("repoPrivate");
  const branchName = localStorage.getItem("branchName");

  try {
    const response = await fetch("/repo_details", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        github_url: githubUrl,
        reponame: repoName,
        branch: branchName,
      }),
    });

    if (!response.ok) {
      document.getElementById("loader").style.display = "none";
      await showToast("Error: Invalid Github URL", "toasterFail");
    } else {
      const data = await response.json();
      displayContents(data.Data);
      await showToast("Success: Valid Github URL", "toasterSuccess");
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader").style.display = "none";
  }
}

async function fetchFolderContents(folderPath) {
  const repoName = localStorage.getItem("repoName");
  const branchName = localStorage.getItem("branchName");

  try {
    const response = await fetch("/fetch_folder_contents", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        folderPath: folderPath,
        reponame: repoName,
        branch: branchName,
      }),
    });

    if (!response.ok) {
      document.getElementById("loader").style.display = "none";
      await showToast("Error: Invalid Github URL", "toasterFail");
    } else {
      const data = await response.json();
      displayContents(data.Data);
      await showToast("Success: Valid Github URL", "toasterSuccess");
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader").style.display = "none";
  }
}

let folderStack = [];
let contentsData = [];
function displayContents(contents) {
  contentsData = contents;
  // const contentsDiv = document.getElementById('contents');
  // contentsDiv.innerHTML = '';  // Clear previous contents

  // contents.forEach(item => {
  //     const element = document.createElement('div');
  //     element.textContent = item.name + (item.type === 'dir' ? '/' : '');  // Add '/' for directories
  //     contentsDiv.appendChild(element);
  // });
  const container = document.getElementById("repositoryContents");
  container.innerHTML = ""; // Clear previous contents
  let folders = {};
  let files = [];
  contents.forEach((item) => {
    debugger;
    const pathComponents = item.split("/");
    if (pathComponents.length === 1) {
      // If there's only one component, it's a file in the root directory
      files.push(item);
    } else {
      // Otherwise, it's a file within a folder
      const folder = pathComponents[0]; // Get the folder name
      const file = pathComponents.slice(1).join("/"); // Get the file path within the folder
      if (!(folder in folders)) {
        folders[folder] = []; // Initialize the folder's contents array if it doesn't exist
      }
      folders[folder].push(file); // Add the file to the folder's contents
    }
  });

  for (const folder in folders) {
    const element = document.createElement("div");
    element.classList.add("repository-item", "folder-item");
    element.textContent = folder;
    element.onclick = () => fetchFolderContents(folder);
    container.appendChild(element);
  }

  files.forEach((file) => {
    const element = document.createElement("div");
    element.classList.add("repository-item");
    element.textContent = file;
    container.appendChild(element);
  });
  document.getElementById("backButton").style.display =
    folderStack.length > 0 ? "block" : "none";
  document.getElementById("submitButton").style.display = "block";
}

function displayFolderContents(folder, files) {
  folderStack.push({ folder: folder, files: files });
  const container = document.getElementById("repositoryContents");
  container.innerHTML = ""; // Clear previous contents

  const folderElement = document.createElement("div");
  folderElement.classList.add("repository-item", "folder-item");
  //   folderElement.textContent = `${folder} (folder)`;
  folderElement.onclick = () => displayContents([...files]);
  container.appendChild(folderElement);

  files.forEach((file) => {
    const fileElement = document.createElement("div");
    fileElement.classList.add("repository-item");
    fileElement.textContent = file;
    container.appendChild(fileElement);
  });
  document.getElementById("backButton").style.display = "block";
}

function goBack() {
  // Pop the top folder from the stack
  folderStack.pop();

  if (folderStack.length > 0) {
    // Display contents of the parent folder
    const { folder, files } = folderStack[folderStack.length - 1];
    displayFolderContents(folder, files);
  } else {
    // If stack is empty, display root contents
    displayContents(contentsData);
  }
}

// document.addEventListener("DOMContentLoaded", async function () {
//   await getRepoDetails();
// });
