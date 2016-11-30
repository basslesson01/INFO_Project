angular.module('SigninApp', [])
  .controller('SigninController', ['$scope', '$http', function($scope, $http) {
    // $scope.message = 'I love JavaScript!';

    var session = {};
    $scope.session = session;
    session['inSession'] = false;
    session['username'] = null;

    $scope.signin = function(user){
      credentials = JSON.stringify({"username": user.username, "password": user.password});
	    // Submit the credentials
      $http.post('https://info3103.cs.unb.ca:43426/signin', credentials).then(function(data){
        // Success here means the transmission was successful - not necessarily the login.
        // The data.status determines login success
        if(data.status == 201){
          // You're in!
          // But does the session carry? Let's try some other endpoint that requires a login
           $http.get('https://info3103.cs.unb.ca:43426/signin').then(function(data){
             session['inSession'] = true;
             $scope.message = "Hello " + user.username + " welcome!";
           });
         }
    });
    }

    $scope.signout = function(){
      $http.delete('https://info3103.cs.unb.ca:43426/signin').then(function(data){
        if(data.status == 200){
          $scope.message = 'Logged out!';
          session['inSession'] = false;
        }else if(data.status == 404){
          $scope.message = 'You are not logged in!'
        }
      });
    }

    $scope.getAllSongs = function(){
      $http.get('https://info3103.cs.unb.ca:43426/signin/songs').then(function(data){
        $scope.message = 'Eh... Testing';
      });
    }

  }]);
