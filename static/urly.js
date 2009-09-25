window.onload = function(){
  var $ = function(id){ return document.getElementById(id) };
  
  var addEvent = function(obj, type, fn){
    if (obj.attachEvent){
      obj['e' + type + fn] = fn;
      obj[type + fn] = function(){ obj['e' + type + fn](window.event) };
      obj.attachEvent('on' + type, obj[type + fn]);
    } else {
      obj.addEventListener(type, fn, false);
    }
  };
  
  var longURL = $('url');
  if (longURL){
    longURL.focus();
  }
  
  var URLform = $('url-form');
  if(URLform){
    addEvent(URLform, 'submit', function(e){
      if (longURL && longURL.value != ''){
        var val = longURL.value = longURL.value.replace('/^\s+|\s+$/g', ''); // trim
        if (!(/^https?:\/\/.*/i).test(val)){
          e.preventDefault();
          longURL.focus();
          longURL.select();
        }
      } else {
        e.preventDefault();
        longURL.focus();
        longURL.select();
      }
    });
  }
  
  var shortURL = $('shorturl');
  if (!shortURL) return;
  
  ZeroClipboard.setMoviePath('/static/ZeroClipboard.swf');
  clip = new ZeroClipboard.Client();
  clip.glue('shorturl-copy');
  var setText = function(){
    clip.setText(shortURL.value);
  };
  clip.addEventListener('load', setText);
  clip.addEventListener('mouseOver', setText);
  
  shortURL.focus();
  shortURL.select();
  addEvent(shortURL, 'focus', function(){
    shortURL.select();
    setText();
  });
};