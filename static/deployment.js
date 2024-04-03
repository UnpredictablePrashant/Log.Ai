document.addEventListener("DOMContentLoaded", async function () {
  const repoName = localStorage.getItem("repoName");
  const port = localStorage.getItem("port");
  document.getElementById("selectedDetails").style.display = "block";
  document.getElementById("price").textContent = "";
  document.getElementById("repoName").textContent = repoName;
});

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
  const loader = (document.getElementById("loader-wrapper").style.display = "");
  const repoName = localStorage.getItem("repoName");
  const port = localStorage.getItem("port");
  try {
    const response = await fetch("/deployment", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reponame: repoName,
        port: port,
      }),
    });

    if (!response.ok) {
      document.getElementById("loader-wrapper").style.display = "none";
      await showToast("Error: Deployment Failed", "toasterFail");
    } else {
      // const data = await response.json();
      // localStorage.setItem("port", port);
      // localStorage.setItem("stack", stack);
      // document.getElementById("message2").innerHTML =
      //   "<a href='" + data.github_url + "'>Jenkins Report</a>";
      // const nextButton = document.getElementById("nextButton");
      // nextButton.style.display = "block";
      document.getElementById("loader-wrapper").style.display = "none";
      await showToast("Success: Deployed", "toasterSuccess");
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader-wrapper").style.display = "none";
  }
}
