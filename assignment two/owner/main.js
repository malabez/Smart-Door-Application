function service(x,y) {
  console.log(x,y);
  callAws(x,y);
}

function callAws(x,y) {
var apigClient;
	apigClient = apigClientFactory.newClient();
  let params = {};
  var visitorImageUrl = "https://facecollectionhw2.s3-us-west-2.amazonaws.com/vijay.jpeg"
  var body = {
    name: x,
    number: y,
    imageUrl: visitorImageUrl
    };
  apigClient
    .valPost(params, body)
    .then(function(result) {
      z = result.data;
      if("errorMessage" in z) alert("Internal server error! visitor could not be added");
      else alert(x + " successfully added!");
      console.log(z);
    })
    .catch(function(result) {
      alert("Internal server error! visitor could not be added");
      console.log(result);
    });
}