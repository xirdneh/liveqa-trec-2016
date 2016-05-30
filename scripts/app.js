/*
Copyright (c) 2015 The Polymer Project Authors. All rights reserved.
This code may only be used under the BSD style license found at http://polymer.github.io/LICENSE.txt
The complete set of authors may be found at http://polymer.github.io/AUTHORS.txt
The complete set of contributors may be found at http://polymer.github.io/CONTRIBUTORS.txt
Code distributed by Google as part of the polymer project is also
subject to an additional IP rights grant found at http://polymer.github.io/PATENTS.txt
*/

(function(document) {
  'use strict';

  // Grab a reference to our auto-binding template
  // and give it some initial binding values
  // Learn more about auto-binding templates at http://goo.gl/Dx1u2g
  var app = document.querySelector('#app');

  // Sets app default base URL
  app.baseUrl = '/liveqa-trec-2016';
  if (window.location.port === '') {  // if production
    // Uncomment app.baseURL below and
    // set app.baseURL to '/your-pathname/' if running from folder in production
    // app.baseUrl = '/polymer-starter-kit/';
  }

  app.displayInstalledToast = function() {
    // Check to make sure caching is actually enabled—it won't be in the dev environment.
    if (!Polymer.dom(document).querySelector('platinum-sw-cache').disabled) {
      Polymer.dom(document).querySelector('#caching-complete').show();
    }
  };

  // Listen for template bound event to know when bindings
  // have resolved and content has been stamped to the page
  app.addEventListener('dom-change', function() {
    console.log('Our app is ready to rock!');
  });

  // See https://github.com/Polymer/polymer/issues/1381
  window.addEventListener('WebComponentsReady', function() {
    // imports are loaded and elements have been registered
  });

  // Main area's paper-scroll-header-panel custom condensing transformation of
  // the appName in the middle-container and the bottom title in the bottom-container.
  // The appName is moved to top and shrunk on condensing. The bottom sub title
  // is shrunk to nothing on condensing.
  window.addEventListener('paper-header-transform', function(e) {
    var appName = Polymer.dom(document).querySelector('#mainToolbar .app-name');
    var middleContainer = Polymer.dom(document).querySelector('#mainToolbar .middle-container');
    var bottomContainer = Polymer.dom(document).querySelector('#mainToolbar .bottom-container');
    var detail = e.detail;
    var heightDiff = detail.height - detail.condensedHeight;
    var yRatio = Math.min(1, detail.y / heightDiff);
    // appName max size when condensed. The smaller the number the smaller the condensed size.
    var maxMiddleScale = 0.50;
    var auxHeight = heightDiff - detail.y;
    var auxScale = heightDiff / (1 - maxMiddleScale);
    var scaleMiddle = Math.max(maxMiddleScale, auxHeight / auxScale + maxMiddleScale);
    var scaleBottom = 1 - yRatio;

    // Move/translate middleContainer
    Polymer.Base.transform('translate3d(0,' + yRatio * 100 + '%,0)', middleContainer);

    // Scale bottomContainer and bottom sub title to nothing and back
    Polymer.Base.transform('scale(' + scaleBottom + ') translateZ(0)', bottomContainer);

    // Scale middleContainer appName
    Polymer.Base.transform('scale(' + scaleMiddle + ') translateZ(0)', appName);
  });

  // Scroll page to top and expand header
  app.scrollPageToTop = function() {
    app.$.headerPanelMain.scrollToTop(true);
  };

  app.closeDrawer = function() {
    app.$.paperDrawerPanel.closeDrawer();
  };


  

})(document);

(function(){
      var that = {};

      that.send = function(src, options) {
        var callback_name = options.callbackName || 'callback',
          on_success = options.onSuccess || function(){},
          on_timeout = options.onTimeout || function(){},
          timeout = options.timeout || 10; // sec

        var timeout_trigger = window.setTimeout(function(){
          window[callback_name] = function(){};
          on_timeout();
        }, timeout * 1000);

        window[callback_name] = function(data){
          window.clearTimeout(timeout_trigger);
          on_success(data);
        };

        var script = document.createElement('script');
        script.type = 'text/javascript';
        script.async = true;
        script.src = src;

        document.getElementsByTagName('head')[0].appendChild(script);
      };
      
  window.$jsonp = that;
})(document);

/*
(function(document){
    document.addEventListener('WebComponentsReady', function(e){
	var askForm = document.querySelector('#ask');
	askForm.addEventListener("submit", function(e){
        e.preventDefault();
        window.$jsonp.send('http://192.168.99.100:8080/liveqa/ask?callback=askHandle', {
            callbackName: 'askHandle',
            onSuccess: function(json){
                console.log('success!', json);
            }, 
            onTimeout: function(){
                console.log('timeout!');
            }, 
            timeout: 5
        });
        return false;
	});

	var testForm = document.querySelector('#test');
	testForm.addEventListener("submit", function(e){
        e.preventDefault();
        window.$jsonp.send('http://192.168.99.100:8080/liveqa/test?callback=testHandle', {
            callbackName: 'testHandle',
            onSuccess: function(json){
                console.log('success!', json);
            }, 
            onTimeout: function(){
                console.log('timeout!');
            }, 
            timeout: 5
        });
        return false;
	});
    });
})(document);
*/

(function(document){
    document.addEventListener('WebComponentsReady', function(e){
	var askForm = document.querySelector('#ask');
	askForm.addEventListener("submit", function(e){
        e.preventDefault();
        document.querySelector('#ask-submit').setAttribute('disabled', true);
        document.querySelector('#ask-paper-submit').disabled = true;
        document.querySelector('#test-submit').setAttribute('disabled', true);
        document.querySelector('#test-paper-submit').disabled = true;
        var ans_div = document.querySelector('#answer');
        ans_div.scrollIntoView();
        ans_div.innerHTML = '<div class="loader"></div><p style="text-align:center;">Coming up with an answer. Please wait.</p> ';
		var r = new XMLHttpRequest(); 
		r.open("POST", "http://104.197.124.71/liveqa/ask", true);
        r.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		r.onreadystatechange = function () {
            var ans_div = document.querySelector('#answer');
			if (r.readyState != 4 || r.status != 200) {
                ans_div.innerHTML = '<p> Sorry, i could not answer this question. Can you try again? </p>';
                document.querySelector('#ask-submit').removeAttribute('disabled');
                document.querySelector('#ask-paper-submit').disabled = false;
                document.querySelector('#test-submit').removeAttribute('disabled');
                document.querySelector('#test-paper-submit').disabled = false;
                return;
            } 
            var resp = JSON.parse(r.responseText);
            //var ans_div = document.querySelector('#answer');
            ans_div.innerHTML = '<h3>Answer</h3>' + 
                    '<p>' + resp.answer.q.best_answer_html + '</p>' + 
                    '<p><b>Jensen-Shannon Distance between the asked question and the answer:</b> ' + resp.answer.jsd + '</p>' +
                    '<p><b>Processing time to answer (approx.): </b> ' + resp.time + 's</p>' + 
                    '<p><b>Resource:</b> <a href="' + resp.answer.q.url + '">' + resp.answer.q.url + '</a>';
            document.querySelector('#ask-submit').removeAttribute('disabled');
            document.querySelector('#ask-paper-submit').disabled = false;
            document.querySelector('#test-submit').removeAttribute('disabled');
            document.querySelector('#test-paper-submit').disabled = false;
		};
		r.send("title=" + askForm.elements.title.value + "&body=" + askForm.elements.body.value);
        return false;
	});

	var testForm = document.querySelector('#test');
	testForm.addEventListener("submit", function(e){
        e.preventDefault();
        document.querySelector('#test-submit').setAttribute('disabled', true);
        document.querySelector('#test-paper-submit').disabled = true;
        document.querySelector('#ask-submit').setAttribute('disabled', true);
        document.querySelector('#ask-paper-submit').disabled = true;
        var ans_div = document.querySelector('#answer');
        ans_div.scrollIntoView();
        ans_div.innerHTML = '<div class="loader"></div><p style="text-align:center;">Coming up with an answer. Please wait.</p> ';
		var r = new XMLHttpRequest(); 
		r.open("POST", "http://104.197.124.71/liveqa/test", true);
        r.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		r.onreadystatechange = function () {
            var ans_div = document.querySelector('#answer');
			if (r.readyState != 4 || r.status != 200){
                ans_div.innerHTML = '<p> Sorry, i could not answer this question. Can you try again? </p>';
                document.querySelector('#test-submit').removeAttribute('disabled');
                document.querySelector('#test-paper-submit').disabled = false;
                document.querySelector('#ask-submit').removeAttribute('disabled');
                document.querySelector('#ask-paper-submit').disabled = false;
                return;
            } 
            var resp = JSON.parse(r.responseText);
            ans_div.innerHTML = '<h3>Question</h3>' + 
                    '<p>' + resp.oq.title + '</p>' + 
                    '<p>' + resp.oq.body + '</p>' +     
                    '<h3>Answer</h3>' + 
                    '<p>' + resp.answer.q.best_answer_html + '</p>' + 
                    '<p><b>Jensen-Shannon Distance between the asked question and the answer:</b> ' + resp.answer.jsd + '</p>' +
                    '<p><b>Processing time to answer (approx.): </b> ' + resp.time + 's</p>' +
                    '<p><b>Resource:</b> <a href="' + resp.answer.q.url + '">' + resp.answer.q.url + '</a>';
            document.querySelector('#test-submit').removeAttribute('disabled');
            document.querySelector('#test-paper-submit').disabled = false;
            document.querySelector('#ask-submit').removeAttribute('disabled');
            document.querySelector('#ask-paper-submit').disabled = false;
		};
		r.send("title=" + askForm.elements.title.value + "&body=" + askForm.elements.body.value);
        return false;
	});
    });
})(document);
