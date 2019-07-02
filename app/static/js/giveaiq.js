function replace_div( hide, show ) {
  document.getElementById(hide).style.display="none";
  document.getElementById(show).style.display="block";
}

function replace_link( posttweetta, tweeterRain ) {
  var result = document.getElementById(posttweetta).value;
  document.getElementById(tweeterRain).data-text=result;
}

function get_tweet_author( tweeturl, destElem ) {
    $(destElem).html('<img src="{{ url_for('static', filename='loading.gif') }}">');
    $.post('/get_tweet_author', {
        tweeturl: $(tweeturl).value()
    }).done(function(response) {
        $(destElem).text(response['text'])
    }).fail(function() {
        $(destElem).text('"{{ _('Error: Could not contact server.') }}"');
    });
}

function replace_rowBox_divs( hideTitle, showTitle, hideContent, showContent, hideFooter, showFooter ) {
  var myClasses = document.querySelectorAll('.rowBoxTitle'),
    i = 0,
    l = myClasses.length;

  for (i; i < l; i++) {
    myClasses[i].style.display = 'none';
  }
  var myClasses = document.querySelectorAll('.rowBoxContent'),
    i = 0,
    l = myClasses.length;

  for (i; i < l; i++) {
    myClasses[i].style.display = 'none';
  }
  var myClasses = document.querySelectorAll('.rowBoxFooter'),
    i = 0,
    l = myClasses.length;

  for (i; i < l; i++) {
    myClasses[i].style.display = 'none';
  }
  document.getElementById(hideTitle).style.display="none";
  document.getElementById(showTitle).style.display="block";
  document.getElementById(hideContent).style.display="none";
  document.getElementById(showContent).style.display="block";
  document.getElementById(hideFooter).style.display="none";
  document.getElementById(showFooter).style.display="block";
}

