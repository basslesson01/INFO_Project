function allCTRL($scope,$http) {
  var session = {};
  $scope.session = session
  session['inSession'] = false
  session['username'] = null

  //login user
  $scope.signin = function(user) {
    var url = 'https://info3103.cs.unb.ca:43426/signin'
    credentials = JSON.stringify({"username": user.username, "password": user.password});

    $http({ method: 'POST', url: url, data: credentials }).then(
      function(response) { // You are logged in!
        if (response.status == 201) {
          $scope.message = "Welcome " + user.username + "! "
          session['inSession'] = true
          session['username'] = response.data.username
        }
      },
      function(response) { // Not success
        $scope.message = "Couldn't log you in"
      }
    );
  }
} // End of allCTRL
