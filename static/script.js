async function showToast(message, toasterId) {
  var toasterElement = document.getElementById(toasterId);
  toasterElement.querySelector(".toast-body").textContent = message;
  var toaster = new bootstrap.Toast(toasterElement);
  toaster.show();
  setTimeout(function () {
    toaster.hide();
  }, 5000);
}
