async function showToast(message, toasterId) {
  var toasterElement = document.getElementById(toasterId);
  toasterElement.querySelector(".toast-body").textContent = message;
  var toaster = new bootstrap.Toast(toasterElement);
  toaster.show();
  setTimeout(function () {
    toaster.hide();
  }, 5000);
}

async function redirectToGitHub() {
  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      document.getElementById("loader").style.display = "none";
      await showToast("Error: Faild to Login", "toasterFail");
    } else {
      const data = await response.json();
      window.location.href = data.Data;
    }
  } catch (error) {
    console.error("Error:", error);
    await showToast("Error: " + error.message, "toasterFail");
  } finally {
    document.getElementById("loader").style.display = "none";
  }
}

//   function redirectToGitHub() {
//     // Replace 'your_client_id' with your GitHub OAuth application's client ID
//     var client_id = "e16b5017df4785ba0140";
//     // Replace 'http://localhost:5000/callback' with your actual callback URL
//     var redirect_uri = "http://127.0.0.1:5001/callback";
//     var github_auth_url = "https://github.com/login/oauth/authorize";
//     var params =
//       "client_id=" +
//       encodeURIComponent(client_id) +
//       "&redirect_uri=" +
//       encodeURIComponent(redirect_uri) +
//       "&scope=user";
//     var auth_url = github_auth_url + "?" + params;
//     window.location.href = auth_url;
//   }
