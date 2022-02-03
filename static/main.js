
function confemail()
{
    var email = document.querySelector('#InputEmail').value;
    var cemail = document.querySelector('#confirmInputEmail').value;
    if(email!=cemail)
    {
    document.querySelector('#sub-button').disabled = true;
    alert("Email adresses do not match")
    }
    else if(email=='')
    {
    document.querySelector('#sub-button').disabled = true;
    alert("Email address field cannot be left blank")
    }
    else
    document.querySelector('#sub-button').disabled = false;
}