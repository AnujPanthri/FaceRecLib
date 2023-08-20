function check_username(elem) {
  if (elem.value != '') {
    fetch(`/user/is_username_available/?username=${elem.value}`, {
      method: 'GET',
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (response) {
        // show a indicator that this username is available
        if (response['available']) {
          // show green indicator
          console.log('Username available');
          elem.dataset.valid = true;
          elem.style.borderColor = 'green';
          elem.style.borderWidth = 4;
        } else {
          // show red indicator
          console.log('Username unavailable');
          elem.dataset.valid = false;
          elem.style.borderColor = 'red';
          elem.style.borderWidth = 4;
        }
      });
  }
}

function check_password_is_matching(confirm_password) {
  var password = document.querySelector('#password');
  if (confirm_password.value != password.value) {
    confirm_password.style.borderColor = 'red';
    confirm_password.style.borderWidth = 4;
  } else {
    confirm_password.style.borderColor = 'green';
    confirm_password.style.borderWidth = 4;
  }
}

function validate_form(form) {
  if (form.username.dataset.valid == 'false') {
    document.querySelector('#container>p').style.visibility = 'visible';
    document.querySelector('#container>p').innerText = 'username not available';
    return false;
  } else if (form.password.value != form.confirm_password.value) {
    document.querySelector('#container>p').style.visibility = 'visible';
    document.querySelector('#container>p').innerText = 'password not matching';
    return false;
  } else {
    return true;
  }
}
