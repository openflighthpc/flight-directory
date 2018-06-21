
var ejectUrl = '/eject/eject.rb'

var $ejectForm = $('#eject-form')
var $ejectCodeInput = $('#eject-code-input')
var $ejectResult = $('#eject-result')

var FORBIDDEN_STATUS = 403

var supportLink = '<a href="mailto:support@alces-flight.com">Alces Flight Support</a>'

var ejectSuccessHtml =
  'Success! Click <a href="/ipa/ui">here</a> to visit your FreeIPA interface.'

var ejectFailureHtml =
  'Incorrect eject code entered. Please contact the ' +
  supportLink +
  ' team if you are encountering difficulty ejecting your Flight Directory.'

var ejectErrorHtml =
  'An error occurred ejecting your Flight Directory. Please contact the ' +
  supportLink
  + ' team for assistance.'


function handleEjectFormSubmit(event) {
  // Clear any existing result.
  $ejectResult.html('')

  $.ajax({
    type: 'POST',
    url: ejectUrl,
    data: $ejectForm.serialize(),
    success: handleEjectSuccess,
    error: handleEjectError,
  })

  // Prevent actual submit.
  event.preventDefault()
}

function handleEjectSuccess() {
  $ejectCodeInput.val('')
  $ejectResult.html(ejectSuccessHtml)
}

function handleEjectError(xhr) {
  var resultHtml

  if (xhr.status === FORBIDDEN_STATUS) {
    // This is expected when the wrong eject code is entered.
    resultHtml = ejectFailureHtml
  }
  else {
    // Any other response status is unexpected.
    resultHtml = ejectErrorHtml
  }

  $ejectResult.html(resultHtml)
}


$ejectForm.submit(handleEjectFormSubmit)
