function nextPage(pageNumber) {
  window.location.href = "stack";
}

function setGitUrl(url) {
  document.getElementById("gitUrlDropdown").innerText = url;
}

async function submitGitUrl() {
  const loader = (document.getElementById("loader-wrapper").style.display = "");
  try {
    debugger;
    const repoName = document.getElementById("repoName").innerText; // Get repo name from inner text
    const repoCloneUrl = document.getElementById("repoCloneUrl").innerText; // Get clone URL from inner text
    const repoLanguage = document.getElementById("repoLanguage").innerText; // Get language from inner text
    const repoPrivate = document.getElementById("repoPrivate").innerText; // Get privacy status from inner text
    const branchName = document.getElementById("branchName").innerText;
    if (repoCloneUrl !== "") {
      if (branchName !== "") {
        const exists = await fetch(
          "https://hellowork-mhlw.vercel.app/api/github?url=" + repoCloneUrl
        ).then((r) => r.json());

        if (exists) {
          await apicall(repoCloneUrl, branchName, repoName);
        } else {
          await showToast("Error: Invalid Github URL", "toasterFail");
        }
      } else {
        await showToast("Select Branch", "toasterFail");
      }
    } else {
      await showToast("Select Repository", "toasterFail");
    }
  } catch (error) {
    console.error("An error occurred during fetch:", error);
    await showToast("Error: Invalid Github URL", "toasterFail");
  } finally {
    document.getElementById("loader-wrapper").style.display = "none";
  }
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

async function apicall(githubUrl, branch_name, repo_name) {
  try {
    const response = await fetch("/configuration", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        github_url: githubUrl,
        branch: branch_name,
        reponame: repo_name,
      }),
    });
    if (!response.ok) {
      document.getElementById("loader-wrapper").style.display = "none";
      await showToast("Error: Invalid Github URL", "toasterFail");
    } else {
      const data = await response.json();
      document.getElementById("message1").innerHTML =
        "<a href='" +
        data.sonarqube_report_url +
        "' target='_blank'>Jenkins Report</a>";
      localStorage.setItem("githubUrl", data.github_url);
      const repoName = document.getElementById("repoName").innerText;
      const repoCloneUrl = document.getElementById("repoCloneUrl").innerText; // Get clone URL from inner text
      const repoLanguage = document.getElementById("repoLanguage").innerText; // Get language from inner text
      const repoPrivate = document.getElementById("repoPrivate").innerText; // Get privacy status from inner text
      const branchName = document.getElementById("branchName").innerText;
      localStorage.setItem("repoName", repoName);
      localStorage.setItem("repoCloneUrl", repoCloneUrl);
      localStorage.setItem("repoLanguage", repoLanguage);
      localStorage.setItem("repoPrivate", repoPrivate);
      localStorage.setItem("branchName", branchName);
      const nextButton = document.getElementById("nextButton");
      nextButton.style.display = "block";

      await showToast("Success: Valid Github URL", "toasterSuccess");
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader-wrapper").style.display = "none";
  }
}

async function fetchGitUrls(githubUrl) {
  try {
    const response = await fetch("/repos", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      document.getElementById("loader-wrapper").style.display = "none";
      await showToast("Error: Invalid Github URL", "toasterFail");
    } else {
      debugger;
      const result = await response.json();
      populateDropdown(result.Data);
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader-wrapper").style.display = "none";
  }
}

function populateDropdown(repos) {
  const dropdownMenu = document.getElementById("dropdownMenu");
  repos.forEach((repo) => {
    const listItem = document.createElement("li");
    listItem.classList.add("dropdown-item");
    listItem.textContent = repo.name;
    listItem.setAttribute("data-clone-url", repo.clone_url);
    listItem.setAttribute("data-language", repo.language);
    listItem.setAttribute("data-private", repo.private);
    listItem.addEventListener("click", function () {
      const selectedRepo = {
        name: repo.name,
        cloneUrl: repo.clone_url,
        language: repo.language,
        private: repo.private,
      };
      showSelectedRepoDetails(selectedRepo);
    });
    dropdownMenu.appendChild(listItem);
  });
}

async function fetchBranches(reponame) {
  try {
    const response = await fetch("/get_branches", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reponame: reponame }),
    });

    if (!response.ok) {
      throw new Error("Failed to fetch branches");
    } else {
      const data = await response.json();
      return data.map((branch) => branch.name);
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
    return [];
  }
}

function showSelectedRepoDetails(selectedRepo) {
  const branchesList = document.getElementById("branchesdropdownMenu");
  branchesList.innerHTML = "";
  document.getElementById("branchesDropdown").textContent = "Select Branches";
  document.getElementById("selectedBranchDetails").style.display = "none";
  document.getElementById("gitUrlDropdown").textContent = selectedRepo.name;
  document.getElementById("repoName").textContent = selectedRepo.name;
  document.getElementById("repoCloneUrl").textContent = selectedRepo.cloneUrl;
  document.getElementById("repoLanguage").textContent = selectedRepo.language;
  document.getElementById("repoPrivate").textContent = selectedRepo.private
    ? "Yes"
    : "No";
  document.getElementById("selectedRepoDetails").style.display = "block";
  fetchBranches(selectedRepo.name)
    .then((branches) => {
      debugger;
      const branchesList = document.getElementById("branchesdropdownMenu");
      branchesList.innerHTML = ""; // Clear previous branches
      branches.forEach((branch) => {
        const listItem = document.createElement("li");
        listItem.classList.add("dropdown-item");
        listItem.textContent = branch;
        listItem.addEventListener("click", function () {
          showSelectedBranch(branch);
        });
        branchesList.appendChild(listItem);
      });
    })
    .catch((error) => console.error("Error fetching branches:", error));
}

function showSelectedBranch(selectedBranch) {
  document.getElementById("branchesDropdown").textContent = selectedBranch;
  document.getElementById("branchName").textContent = selectedBranch;
  document.getElementById("selectedBranchDetails").style.display = "block";
}
async function fetchGitRepoDetails(githubUrl) {
  try {
    const response = await fetch("/repos", {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      document.getElementById("loader-wrapper").style.display = "none";
      await showToast("Error: Invalid Github URL", "toasterFail");
    } else {
      debugger;
      const result = await response.json();
      populateDropdown(result.Data);
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader-wrapper").style.display = "none";
  }
}

// Fetch Git URLs when the page loads
document.addEventListener("DOMContentLoaded", async function () {
  await fetchGitUrls();
});
