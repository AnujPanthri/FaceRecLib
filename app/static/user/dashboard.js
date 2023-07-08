var dragged_elem;
var features_updated=false;
var touch_start_time=null;
var elapsedTime=null;
var maxAllowedTime=500;

function drag(ev){
    // ev.preventDefault();
    console.log(ev.target.id);
    dragged_elem=ev.target;
    // ev.dataTransfer.setData("text",ev.target.id);
}

function dragTouchstart(e,elem) {
    elapsedTime=null;
    touch_start_time = new Date().getTime();
}
function dragTouchmove(e,elem) {

    let touchX = e.touches[0].pageX;
    let touchY = e.touches[0].pageY;

    if(elapsedTime==null)
    {
        elapsedTime = new Date().getTime() - touch_start_time;
    }
    
    // console.log(elapsedTime);
    
    if (elapsedTime<maxAllowedTime) return;
    
    // console.log("no-scroll")
    e.preventDefault()
    
    if (dragged_elem==null)
    {
        dragged_elem=elem;
        console.log(dragged_elem);
    }

}

function allowDrop(ev){
    ev.preventDefault();
    console.log("ready to be dropped");
}

function drop(ev,element){
    ev.preventDefault();
    console.log("dropped!");
    element.appendChild(dragged_elem);
    dragged_elem=null;
    features_updated=false;
    
}

function dragTouchend(e,elem) {
    
    if(dragged_elem==null) return;
    
    var droppable_element=document.elementFromPoint(e.changedTouches[0].clientX, e.changedTouches[0].clientY).closest(".droppable");
    if(droppable_element==null) return;
    
    if(droppable_element.hasAttribute("data-dropto"))   droppable_element=droppable_element.querySelector(droppable_element.dataset.dropto)
    
    droppable_element.appendChild(dragged_elem);
    
    console.log(droppable_element)
    dragged_elem=null;
    features_updated=false;
    // e.target.style.transform="scale(0.8)";
  }



function count_words(elem){
    var count = 0;
          
    // Split the words on each
    // space character 
    var split = elem.value.split(' ');
    
    // Loop through the words and 
    // increase the counter when 
    // each split word is not empty
    for (var i = 0; i < split.length; i++) {
        if (split[i] != "") {
            count += 1;
        }
    }
    console.log("count:",count)
}

document.querySelector("#api-key>.copy").addEventListener("click",function(e){
    var key_tag=document.querySelector("#api-key>p");
    key_tag.focus();
    console.log(key_tag.innerText);
    navigator.clipboard.writeText(key_tag.innerText);
})


document.querySelector("#api-key>.refresh").addEventListener("click",function(e){
    var key_tag=document.querySelector("#api-key>p");
    fetch("update_key/").then(function(response){
         return response.json();
    }).then(function(response){
        console.log(response);
        if ("key" in response){
            key_tag.innerText=response["key"];
        }
    });
})  





function deselect(e,elem){
    // document.body.focus();

    if(e.key=="Enter")
        elem.blur();
    else if(elem.value!=elem.dataset.name)
        features_updated=false;
}


function remove_remark(remark){
    var unassigned_faces=document.querySelector("#unassigned_faces");
    var all_crops=remark.querySelectorAll("#remark_list>.remark>.faces>img");
    all_crops.forEach(function(crop){
        unassigned_faces.appendChild(crop);
    })
    remark.remove();
}


function add_remark(){
    // make such a structure:
    // <div class="remark" ondragover="allowDrop(event)" ondrop="drop(event,this)">
    // <input type="text" value="Anuj" ondrop="return false;" onkeypress="deselect(event,this);">
    // <div class="faces"></div>
    // <i class="fa-solid fa-xmark" onclick="this.parentElement.remove();"></i>
    // </div>
    var remark=document.createElement("div");
    remark.setAttribute("class","remark droppable");
    remark.dataset.dropto=".faces";
    remark.setAttribute("ondragover","allowDrop(event)");
    remark.setAttribute("ondrop","drop(event,this.querySelector('#remark_list>.remark>.faces'))");
    var name=document.createElement("input");
    name.setAttribute("type","text");
    name.setAttribute("ondrop","return false;");
    name.setAttribute("onkeyup","deselect(event,this);");
    var faces=document.createElement("div");
    faces.setAttribute("class","faces");
    var close_icon=document.createElement("i");
    close_icon.setAttribute("class","fa-solid fa-xmark");
    close_icon.setAttribute("onclick","remove_remark(this.parentElement);");
    remark.appendChild(name);
    remark.appendChild(faces);
    remark.appendChild(close_icon);
    document.querySelector("#remark_list").appendChild(remark);
    name.focus();
    // name.select();

}


function filterFunction() {
    var input, filter, ul, li, a, i;
    input = document.getElementById("myInput");
    filter = input.value.toUpperCase();
    div = document.getElementById("myDropdown");
    a = div.getElementsByTagName("a");
    for (i = 0; i < a.length; i++) {
      txtValue = a[i].textContent || a[i].innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        a[i].style.display = "";
      } else {
        a[i].style.display = "none";
      }
    }
  }



  var database_input=document.querySelector("#database-form>.field>.add_button>input")
  database_input.addEventListener("change", function(e){
      if(e.target.files[0]){
          console.log(e.target.files[0].name);
          
          const formdata = new FormData();
          formdata.append("image",e.target.files[0]);
          show_loading_bar()
          
          fetch("get_crops/",
          {
              method:'POST',
              body:formdata,
          }).then(
              function(response)
              {
                  return response.json();
              }
          ).then(
              function(response)
              {
                  hide_loading_bar()
                  console.log(response);
                
                  if (response['message']=='successful')
                  {
                    // add crops to the #unassigned_faces                      
                    var crop_container=document.querySelector("#unassigned_faces");
                      for(var i=0;i<response["crops"].length;i++)
                      {
                          
                          var crop_img=document.createElement("img");
                          crop_img.src="data:image/jpeg;base64,"+response["crops"][i].split('\'')[1];                          
                          crop_img.setAttribute("class","crop_img");
                          // crop_img.setAttribute("id",crop_img.dataset.image_name+'\\'+crop_img.dataset.crop_name);
                          crop_img.setAttribute("draggable","true");
                          crop_img.setAttribute("ondragstart","drag(event)");
                          crop_container.appendChild(crop_img)

                          // disable right click
                          crop_img.addEventListener("contextmenu",function(ev){ev.preventDefault();});
                          //make it work with touch
                          crop_img.setAttribute("ontouchstart","dragTouchstart(event,this);");
                          crop_img.setAttribute("ontouchmove","dragTouchmove(event,this);");
                          crop_img.setAttribute("ontouchend","dragTouchend(event,this);");
  
                      }
                      
                      // response['images'].forEach(img_name => {
                      //     img_tag=document.createElement("img");
                      //     img_tag.src=Flask.url_for('upload',{subfolder:'images',filename:img_name} );
                      //     images_div.appendChild(img_tag);
                      // });
                  }
                  
  
              }
          );
      }
  });


function update_db_crops(elem)
  {
      var all_remarks={};
      var num_of_remarks=0;
      
      var face_remarks=document.querySelectorAll("#remark_list>.remark");
      
      for (var i=0;i<face_remarks.length;i++)
      {
          var faces=face_remarks[i].querySelectorAll("#remark_list>.remark>.faces>img");
          var face_base64_list=[]
          if (faces.length>0)
          {
              for(var j=0;j<faces.length;j++)
              {
                face_base64_list.push(faces[j].src.split(',',2)[1])
              }
              all_remarks[face_remarks[i].querySelector("input").value]=face_base64_list;
              
              num_of_remarks+=1;
              
          }
          
      }
  
      if (num_of_remarks>0)
      {

        var alldata={};
        alldata["person_name"]=document.querySelector("#database-form>.field>.person_name").value;
        alldata["remarks"]=all_remarks;
        console.log(alldata);
        show_loading_bar();
        
          
          fetch("set_crops/",{
              method:"POST",
              headers: { "Content-Type": "application/json"},
              body:JSON.stringify(alldata)
          }).then(function(response){
              return response.json();
          }).then(function(response){
                hide_loading_bar();
                console.log(response);
                var person_ids=document.querySelectorAll("#db_people_table>tr>td:first-child");
                var matching_person_id=null;
                person_ids.forEach(element => {
                    if(element.innerText==alldata["person_name"])
                    {
                        element.parentElement.remove();
                        // element
                    }
                });
                alldata["remarks"]
                add_person_row(alldata["person_name"],Object.keys(alldata["remarks"]).join(","));
                
          });
  
      }
      else{
          console.log("add database faces first");
      }
      
  
      
  }

function face_recoginization(elem){
    if(elem.files[0]){
        formdata=new FormData();
        formdata.append("image",elem.files[0]);
        show_loading_bar();
        fetch("face_recognize/",{
            method:"POST",
            body:formdata
        }).then(function(response){
            return response.json();
        }).then(function(response){
            hide_loading_bar();
            console.log(response);
            document.querySelector("#face_recognition_image").src="data:image/jpeg;base64,"+response["pred_image"].split('\'')[1];                          
            document.querySelector("#face_recognition_image").style.width="unset";
        })
    }
}





function add_person_row(person_id,remarks)
{
//#db_people_table
// <tr>
//    <td>anuj</td>
//    <td>Front_face</td>
//
//    <td>
//        <button class="remove"><i class="fa-solid fa-close"></i></button>
//    </td>
// </tr>
    var table_row=document.createElement("tr");
    var person_id_tag=document.createElement("td");
    person_id_tag.innerText=person_id;
    var remarks_tag=document.createElement("td");
    remarks_tag.innerText=remarks;
    
    var remove_tag=document.createElement("td");
    remove_tag.innerHTML='<button class="remove" onclick="delete_person(this);"><i class="fa-solid fa-close"></i></button>';
    table_row.appendChild(person_id_tag);
    table_row.appendChild(remarks_tag);
    table_row.appendChild(remove_tag);
    
    // document.querySelector("#db_people_table").appendChild(table_row);
    var table=document.querySelector("#db_people_table > tbody");
    table.after(table_row);
}


// get_all_persons_from_db/
fetch("get_all_persons_from_db/").then(function(response){
    return response.json();
}).then(function(response){
    console.log(response);
    for (var i=0 ; i<response['person_ids'].length;i++){
        add_person_row(response['person_ids'][i],response['remarks'][i])
    }
})




function delete_person(elem){
    // console.log(elem);
    console.log(elem.getAttribute("class"));   
    var row=elem.parentNode.parentNode;
    // username:row.firstChild.innerText

    if (elem.getAttribute("class")=="remove")
    {
        const response = confirm("Are you sure you want to do that?");
        if (!response)
        {
            return;
        }
    }

    
    fetch("remove_person_from_db/",{
        method:"POST",
        headers: { "Content-Type": "application/json"},
        body:JSON.stringify({"person_id":row.firstChild.innerText})
    }).then(function(response){
        return response.json();
    }).then(function(response){
        console.log("response:",response);
        
        row.remove();
    })
    
    
    
}


function show_settings(){
    document.querySelector('#settings_menu').style.display='block';
    document.querySelector('#container').classList.add("blur");
    // add click outside to close settings
    document.addEventListener("click",close_settings);
}
function close_settings(event){
    if ((!document.querySelector('#settings_menu').contains(event.target))&& (!event.target.classList.contains("settings_btn")))
        hide_settings();
}
function hide_settings(){
    document.querySelector('#settings_menu').style.display='none';
    document.querySelector('#container').classList.remove("blur");
    document.removeEventListener("click",close_settings);
}

function update_settings_html(res){
    p_thres.value=p_thresValue.innerText=res['p_thres'];
    nms_thres.value=nms_thresValue.innerText=res['nms_thres'];
    
    small_size.value=small_sizeValue.innerText=res['small_size'];
    large_size.value=large_sizeValue.innerText=res['large_size'];

    d_thres.value=d_thresValue.innerText=res['d_thres'];
    a_thres.value=a_thresValue.innerText=res['a_thres'];

    db_mode.value=res['db_mode'];
    fr_mode.value=res['fr_mode'];
    // console.log(res['db_mode'],res['fr_mode']);
}


function get_settings(){
    fetch("get_settings/",{
        method:"GET"
    }).then(function(response){
        return response.json();
    }).then(function(res){
        console.log(res);
        update_settings_html(res);
        
    })
}
get_settings();
// document.querySelector('#p_thres')
// document.querySelector('#p_thres').value

function update_settings(){
    var new_settings=new Object();
    new_settings['p_thres']=p_thres.value;
    new_settings['nms_thres']=nms_thres.value;
    new_settings['small_size']=small_size.value;
    new_settings['large_size']=large_size.value;
    new_settings['d_thres']=d_thres.value;
    new_settings['a_thres']=a_thres.value;
    new_settings['db_mode']=db_mode.value;
    new_settings['fr_mode']=fr_mode.value;
    
    fetch("update_settings/",{
        method:"POST",
        headers:{'content-type': 'application/json'},
        body:JSON.stringify(new_settings)
    }).then(function(response){
        return response.json();
    }).then(function(res){
        console.log(res);
        if(res['message']=='success')
            hide_settings();
    }
    );
}

function reset_settings(){
    fetch("reset_settings/",{
        method:"GET"
    }).then(function(response){
        return response.json();
    }).then(function(res){
        console.log(res);
        if(res['message']=='success')
            update_settings_html(res);
    }
    );
}


var loader=document.querySelector(".loader");

function show_loading_bar(){
    loader.classList.remove("hidden");
}

function hide_loading_bar(){
    loader.classList.add("hidden");
}