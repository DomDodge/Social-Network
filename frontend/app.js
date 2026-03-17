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
  vm.recommendations = [];

  vm.signup = function() {
    $http.post(BASE + '/signup', vm.signupData)
      .then(function(res) {
        vm.user = vm.signupData.username;
        vm.signupData = {};
        vm.loadPosts();
        vm.loadFeed();
        vm.loadRecommendations();
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
        vm.loadRecommendations();
      }, function(err) {
        alert(err.data && err.data.error ? err.data.error : 'Login failed');
      });
  };

  vm.logout = function() {
    vm.user = null;
    vm.feed = [];
    vm.recommendations = [];
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

    // Check if the current user is already in the likes array
    var hasLiked = post.likes && post.likes.includes(vm.user);
    var method = hasLiked ? 'DELETE' : 'POST';

    // We use the full $http config object here so we can specify POST or DELETE
    $http({
      method: method,
      url: BASE + '/posts/' + post.id + '/like',
      data: { username: vm.user },
      headers: { 'Content-Type': 'application/json' }
    }).then(function() {
      // Optimistic UI: Update the array locally so the screen changes instantly 
      // without needing to refresh the whole feed from the database
      if (!post.likes) post.likes = [];
      
      if (hasLiked) {
        // Remove the user from the likes array
        post.likes = post.likes.filter(function(u) { return u !== vm.user; });
      } else {
        // Add the user to the likes array
        post.likes.push(vm.user);
      }
    });
  };

  // Fetch comments for a specific post
  vm.loadComments = function(post) {
    $http.get(BASE + '/posts/' + post.id + '/comments')
      .then(function(res) {
        // Attach the comments array directly to the post object so Angular can render it
        post.comments = res.data; 
      });
  };

  vm.loadRecommendations = function() {
    if (!vm.user) return;
    $http.get(BASE + '/recommendations/' + vm.user).then(function(res) {
      vm.recommendations = res.data;
    });
  };

  // Submit a new comment
  vm.addComment = function(post) {
    if (!vm.user || !post.newCommentText) {
      alert('You must be logged in and write a comment!');
      return; 
    }
    
    $http.post(BASE + '/posts/' + post.id + '/comments', { 
      username: vm.user, 
      content: post.newCommentText 
    }).then(function() {
      post.newCommentText = ''; // Clear the input field after posting
      vm.loadComments(post);    // Refresh the comments to show the new one
    });
  };

  vm.followUser = function(username) {
    if (!vm.user) { alert('Login required'); return; }
    $http.post(BASE + '/follow', { follower: vm.user, following: username })
      .then(function() {
        vm.loadFeed();
        vm.loadRecommendations();
      });
  };

  // initialize
  vm.loadPosts();
}]);
// ...existing code...