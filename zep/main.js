App.addOnKeyDown(81,function(p){
	//Displays the nicknames of all players in the chat window via App.players
	let players = App.players;
	for(let i in players){
		let player = players[i]
		App.sayToAll(player.id)
	}
});

let blueman = App.loadSpritesheet("board.png");
let blueman2 = App.loadSpritesheet("board.png");

// App.onInit.Add(function(){
//   Map.putObject(23, 48, blueman, { overlap: true })
// })
let touched = {};
App.onJoinPlayer.Add(function(player){
  player.tag = {
		widget: null,
    uniqkey: Math.floor(100000000 + Math.random() * 900000000)
	};
	player.title = null;
	player.sendUpdated();
  Map.putObject(14, 34, blueman, { overlap: true });
  Map.putObject(36, 33, blueman, { overlap: true });
  touched[14+34] = false;
  touched[36+33] = false;
})

App.addOnLocationTouched("mcdonalds", function(player){
	App.sayToAll("has arrived at myLocation.")
  App.httpGet(
    `https://flaskzeptest.herokuapp.com/get_level?name=${player.id}&company=mcdonalds`,
    null,
    function (res) {
      // Change the response to a json object
      App.sayToAll(res);
      if(player.title) player.title = null;
      else player.title = res;
    }
  );
  player.sendUpdated();
});

App.addOnLocationTouched("starbucks", function(player){
	App.sayToAll("has arrived at starbucks.")
  App.httpGet(
    `https://flaskzeptest.herokuapp.com/get_level?name=${player.id}&company=starbucks`,
    null,
    function (res) {
      // Change the response to a json object
      App.sayToAll(res);
      if(player.title) player.title = null;
      else player.title = res;
    }
  );
  
  player.sendUpdated();
});

App.onObjectTouched.Add(function(sender, x, y, tileID){
  App.sayToAll(`${x} ${y}`)
  if(!touched[x+y]){
    touched[x+y] = true;
    Map.putObject(x, y, null)
    // Executes when a player enters
    let store = (x+y != 69) ? "mcdonalds" : "starbucks"
    sender.tag.widget = sender.showWidget("widget.html", "top", 400, 600); // Display
    sender.tag.widget.sendMessage({
      text: "Take a picture with a " + store + " store at the background",
      key: sender.tag.uniqkey
    });
    sender.tag.widget.onMessage.Add(function (sender, msg) {
      // Closes the widget when the 'type: close' message is sent from the widget to the App 
      App.sayToAll(tileID);
      if (msg.type == "close" && sender.tag.widget) {
        sender.showCenterLabel("Widget has been closed.");
        sender.tag.widget.destroy();
        sender.tag.widget = null;
        Map.putObject(x, y, blueman, {overlap: true})
        touched[x+y] = false;
        sender.spawnAt(x+1, y+1);
      }
      else if(msg.type == "request" && sender.tag.widget){
        App.sayToAll("request from server")
        App.httpGet(
          `https://flaskzeptest.herokuapp.com/check_quest?name=${sender.id}&uniq=${sender.tag.uniqkey}&hashtag=${store}`,
          null,
          function (res) {
            // Change the response to a json object
            sender.tag.widget.sendMessage({
              text: JSON.parse(res).message,
              key: sender.tag.uniqkey
            });
          }
        );
      }
    });
  }
  
});

