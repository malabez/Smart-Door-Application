function service(x) {
  console.log(x);
  callAws(x);
}

function callAws(x) {
  var apigClient = apigClientFactory.newClient();
  let params = {};
  let additionalParams = {};
  var body = {
    "message" : x
  };
  apigClient.valPost(params, body, additionalParams)
    .then(function(result) {
      x = result.data.body;
      alert("Welcome "+x.visitorName);
      console.log(x);
    })
    .catch(function(result) {
      console.log(result);
    });
}


