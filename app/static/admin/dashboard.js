function add_request_row(username, request_message) {
  //#access_requests_table
  // <tr>
  //    <td>abc</td>
  //    <td>Please give access :(</td>
  //
  //    <td>
  //        <button class="accept"><i class="fa-solid fa-check"></i></button>
  //        <button class="reject"><i class="fa-solid fa-close"></i></button>
  //    </td>
  // </tr>
  var table_row = document.createElement('tr');
  var username_tag = document.createElement('td');
  username_tag.innerText = username;
  var request_message_tag = document.createElement('td');
  request_message_tag.innerText = request_message;

  var review_tag = document.createElement('td');
  review_tag.innerHTML =
    '<button class="accept" onclick="perform_action(this);"><i class="fa-solid fa-check"></i></button>\
                          <button class="reject" onclick="perform_action(this);"><i class="fa-solid fa-close"></i></button>';
  table_row.appendChild(username_tag);
  table_row.appendChild(request_message_tag);
  table_row.appendChild(review_tag);
  document.querySelector('#access_requests_table').appendChild(table_row);
}

fetch('get_all_requests/')
  .then(function (response) {
    return response.json();
  })
  .then(function (response) {
    console.log(response);
    if ('username' in response) {
      for (var i = 0; i < response['username'].length; i++) {
        if (response['access_key'][i] == null)
          add_request_row(
            response['username'][i],
            response['request_message'][i],
          );
        else
          add_access_row(
            response['username'][i],
            response['request_message'][i],
          );
      }
    }
  });

function perform_action(elem) {
  // console.log(elem);
  console.log(elem.getAttribute('class'));
  var row = elem.parentNode.parentNode;
  // username:row.firstChild.innerText

  if (elem.getAttribute('class') == 'reject') {
    const response = confirm('Are you sure you want to do that?');
    if (!response) {
      return;
    }
  }

  var formdata = new FormData();
  formdata.append('username', row.firstChild.innerText);
  formdata.append('mode', elem.getAttribute('class'));
  fetch('update_requests/', {
    method: 'POST',
    body: formdata,
  })
    .then(function (response) {
      return response.json();
    })
    .then(function (response) {
      console.log('response:', response);
      if (elem.getAttribute('class') == 'accept') {
        add_access_row(
          row.firstChild.innerText,
          row.querySelector('td:nth-child(2)').innerText,
        );
      } else if (elem.getAttribute('class') == 'revoke') {
        add_request_row(
          row.firstChild.innerText,
          row.firstChild.dataset.request_message,
        );
      }
      row.remove();
    });
}

function add_access_row(username, request_message) {
  //#access_requests_table
  // <tr>
  //    <td>username</td>
  //    <td>
  //        <button class="reject"><i class="fa-solid fa-close"></i></button>
  //    </td>
  // </tr>
  var table_row = document.createElement('tr');
  var username_tag = document.createElement('td');
  username_tag.innerText = username;
  username_tag.dataset.request_message = request_message;
  var remove_access_tag = document.createElement('td');
  remove_access_tag.innerHTML =
    '<button class="revoke" onclick="perform_action(this);"><i class="fa-solid fa-close"></i></button>';
  table_row.appendChild(username_tag);
  table_row.appendChild(remove_access_tag);
  document.querySelector('#access_granted_table').appendChild(table_row);
}

// add_access_row('username')
// add_access_row('anuj')
// add_access_row('abc')
