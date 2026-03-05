// ...existing code...
angular.module('socialApp', [])
.controller('MainCtrl', ['$http', '$window', function($http, $window) {
  var vm = this;
  var BASE = 'http://127.0.0.1:5000';

  vm.user = null;
  vm.signupData = {};
  vm.loginData = {};
  vm.newPost = '';
  vm.posts = [];
  vm.feed = [];

  vm.signup = function() {
    $http.post(BASE + '/signup', vm.signupData)
      .then(function(res) {
        vm.user = vm.signupData.username;
        vm.signupData = {};
        vm.loadPosts();
        vm.loadFeed();
      }, function(err) {
        alert(err.data && err.data.error ? err.data.error : 'Signup failed');
      });
  };

  vm.login = function() {
    $http.post(BASE + '/login', vm.loginData)
      .then(function(res) {
        // if account exists return username, else rely on email
        if (res.data && res.data.account && res.data.account.username) {
          vm.user = res.data.account.username;
        } else {
          vm.user = vm.loginData.username;
        }
        vm.loginData = {};
        vm.loadFeed();
      }, function(err) {
        alert(err.data && err.data.error ? err.data.error : 'Login failed');
      });
  };

  vm.logout = function() {
    vm.user = null;
    vm.feed = [];
  };

  vm.createPost = function() {
    if (!vm.newPost || !vm.user) return;
    $http.post(BASE + '/posts', { username: vm.user, content: vm.newPost })
      .then(function() {
        vm.newPost = '';
        vm.loadPosts();
        vm.loadFeed();
      });
  };

  vm.loadPosts = function() {
    $http.get(BASE + '/posts').then(function(res) {
      vm.posts = res.data;
    });
  };

  vm.loadFeed = function() {
    if (!vm.user) return;
    $http.get(BASE + '/feed/' + vm.user).then(function(res) {
      vm.feed = res.data;
    });
  };

  vm.like = function(post) {
    if (!vm.user) { alert('Login required'); return; }
    $http.post(BASE + '/posts/' + post.id + '/like', { username: vm.user })
      .then(function() {
        // no-op; optimistic UI
      });
  };

  vm.followUser = function(username) {
    if (!vm.user) { alert('Login required'); return; }
    $http.post(BASE + '/follow', { follower: vm.user, following: username })
      .then(function() {
        vm.loadFeed();
      });
  };

  // initialize
  vm.loadPosts();
}]);
// ...existing code...