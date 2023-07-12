var dragged_elem;
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
    
}

function dragTouchend(e,elem) {
    
    if(dragged_elem==null) return;
    
    var droppable_element=document.elementFromPoint(e.changedTouches[0].clientX, e.changedTouches[0].clientY).closest(".droppable");
    if(droppable_element==null) return;
    
    if(droppable_element.hasAttribute("data-dropto"))   droppable_element=droppable_element.querySelector(droppable_element.dataset.dropto)
    
    droppable_element.appendChild(dragged_elem);
    
    console.log(droppable_element)
    dragged_elem=null;
    // e.target.style.transform="scale(0.8)";
  }

// function click_based_drop(elem)
// {
//     if(dragged_elem!=null){

//         console.log("asd");
//         if(elem.getAttribute("class")=="person")
//         {
//             console.log();
//             elem.querySelector(".faces").appendChild(dragged_elem);
//             dragged_elem=null;
//             features_updated=false;
//         }
//         else if (elem.getAttribute("id")=="unassigned_faces")
//         {
//             document.querySelector("#unassigned_faces").appendChild(dragged_elem);
//             dragged_elem=null;
//             features_updated=false;
//         }
//     }
    
// }


var database_input=document.querySelector("#db_images_bar>.add_button>input")
database_input.addEventListener("change", function(e){
    if(e.target.files[0]){
        console.log(e.target.files[0].name);
        
        const formdata = new FormData();
        formdata.append("a",23);
        formdata.append("image",e.target.files[0]);
        
        var loader_txt=show_loading_bar();
        const myInterval=start_timer(loader_txt,0.2);
        
        fetch("/demo/add_crops/",
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
                console.log(response);
                if (response['message']=='successful')
                {
                    clearInterval(myInterval);
                    hide_loading_bar();
                    var images_div=document.querySelector("#db_images_bar>#db_images");
                    var img_container_tag=document.createElement("div");
                    var img_remove_tag=document.createElement("p");
                    var img_tag=document.createElement("img");
                    img_tag.src="data:image/jpeg;base64,"+response['image'];
                    img_tag.setAttribute("class","db_image");
                    img_remove_tag.setAttribute("class","close_text");
                    img_remove_tag.innerHTML="✖";
                    img_container_tag.setAttribute("class","db_image_container");
                    img_container_tag.setAttribute("onclick","remove_image(this);");
                    img_container_tag.dataset.image_name=response['image_name'];
                    img_container_tag.appendChild(img_tag);
                    img_container_tag.appendChild(img_remove_tag);
                    
                    img_container_tag.addEventListener("mouseenter",function(e){

                        var image=document.querySelector("#face_rec_image");
                        if (image.hasAttribute('src'))
                        {
                            image.dataset.old_src=image.src;
                        }
                        image.src=e.target.querySelector("img").src;
                        

                    })
                    img_container_tag.addEventListener("mouseleave",function(){
                        
                        var image=document.querySelector("#face_rec_image");
                        if (image.hasAttribute("data-old_src")){
                            console.log("has_old_src")
                            image.src=image.dataset.old_src;
                            delete image.dataset.old_src;
                        }
                        else{
                            image.removeAttribute('src');
                        }
                        

                    })

                    images_div.appendChild(img_container_tag);

                    
                    

                    // add crops to the #unassigned_faces
                    for(var i=0;i<response["crops"].length;i++)
                    {
                        var crop_container=document.querySelector("#unassigned_faces");
                        var crop_img=document.createElement("img");
                        crop_img.src="data:image/jpeg;base64,"+response["crops"][i];
                        crop_img.dataset.image_name=response['image_name'];
                        
                        crop_img.setAttribute("class","crop_img");
                    
                        crop_img.setAttribute("draggable","true");
                        crop_img.setAttribute("ondragstart","drag(event)");
                        crop_container.appendChild(crop_img)

                        // disable right click
                        crop_img.addEventListener("contextmenu",function(ev){
                            ev.preventDefault();
                            // console.log("right click");
                            // ev.target.style.transform="scale(1.2)";
                            // ev.target.focus();
                            // dragged_elem=e.target;
                         }); 
                        
                        // crop_img.addEventListener("blur",function(ev){
                        //     console.log("blur");
                        //     ev.target.style.transform="scale(1)";
                        //  }); 
                     
                        
                        // add touch events
                        // crop_img.addEventListener("touchstart",function(e){
                        //     console.log("touch-started");
                        // });
                        crop_img.setAttribute("ontouchstart","dragTouchstart(event,this);");
                        crop_img.setAttribute("ontouchmove","dragTouchmove(event,this);");
                        crop_img.setAttribute("ontouchend","dragTouchend(event,this);");
                        // crop_img.addEventListener("touchmove",function(e){
                            
                        //     dragTouchmove(e);
                        // });
                        // crop_img.addEventListener("touchend",function(e){
                        //     console.log("touch-end");
                        //     dragTouchend(e);
                        // });
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




function remove_image(e)
{
    // reset old image in image-viewer start ----------------------------------------
    var image=document.querySelector("#face_rec_image");
                        if (image.hasAttribute("data-old_src")){
                            console.log("has_old_src")
                            image.src=image.dataset.old_src;
                            delete image.dataset.old_src;
                        }
                        else{
                            image.removeAttribute('src');
                        }
    // reset old image in image-viewer end ------------------------------------------

    // console.log(e)
    
    crops=document.querySelectorAll(`.crop_img[data-image_name='${e.dataset.image_name}']`)
    // console.log(crops)
    for(var i=0;i<crops.length;i++)
        crops[i].remove();
    
    e.remove();
}




function add_person(){
    // make such a structure:
    // <div class="person" ontouchend="dragTouchend(event)" ondragover="allowDrop(event)" ondrop="drop(event,this)">
    // <input type="text" value="Anuj" ondrop="return false;" onkeypress="deselect(event,this);">
    // <div class="faces"></div>
    // <i class="fa-solid fa-xmark" onclick="this.parentElement.remove();"></i>
    // </div>
    var person=document.createElement("div");
    person.setAttribute("class","person droppable");
    person.dataset.dropto=".faces";
    person.setAttribute("ondragover","allowDrop(event)");
    person.setAttribute("ondrop","drop(event,this.querySelector('.faces'))");
    // person.setAttribute("ontouchend","dragTouchend(event)");
    var name=document.createElement("input");
    name.setAttribute("type","text");
    name.setAttribute("ondrop","return false;");
    name.setAttribute("onkeyup","deselect(event,this);");
    var faces=document.createElement("div");
    faces.setAttribute("class","faces");
    var close_icon=document.createElement("i");
    close_icon.setAttribute("class","fa-solid fa-xmark");
    close_icon.setAttribute("onclick","remove_person(this.parentElement);");
    person.appendChild(name);
    person.appendChild(faces);
    person.appendChild(close_icon);
    document.querySelector("#name_list").appendChild(person);
    name.focus();
    // name.select();

}

function load_image_preview(elem){
    if(elem.files[0])
    {
        console.log(elem.files[0]);
        if (FileReader && elem.files[0]) {
            var fr = new FileReader();
            fr.onload = function () {
                document.querySelector("#face_rec_image").src = fr.result;
                document.querySelector("#face_rec_image").style.width="unset";
            }
            fr.readAsDataURL(elem.files[0]);
        }
    }
}

function deselect(e,elem){
    // document.body.focus();

    if(e.key=="Enter")
        elem.blur();
}

function update_crops_labels(elem)
{
    console.log("update face labels");
    var formdata=new FormData();
    
    var faces=document.querySelectorAll(".person>.faces>img");
    var faces_base64=[]
    var selected_faces=[]

    for (var i=0;i<faces.length;i++)
    {
        
        if(!faces[i].hasAttribute("data-features"))
        {
            selected_faces.push(faces[i]);
            faces_base64.push(faces[i].src.split(',')[1]); // also removed datajpeg  part
        }
    
    }

    if (selected_faces.length>0)
    {
        formdata.append("faces",faces_base64);
        // to see the the json
        // var object = {};
        // formdata.forEach(function(value, key){
        //     object[key] = value;
        // });
        // var json = JSON.stringify(object);
        // console.log(json);
        
        fetch("/demo/update_crops_labels/",{
            method:"POST",
            body:formdata
        }).then(function(response){
            console.log(response)
            return response.json();
        }).then(function(response){
            console.log(response);
            if (response.message!='success') return;
            
            for(var i=0;i<response['features'].length;i++)
                selected_faces[i].dataset.features=response['features'][i];
            face_recognition(elem);
            });
        
        }
    else{
        console.log("already up to date !");
        face_recognition(elem);
    }
        
    
}



function face_recognition(elem)
{

    if(elem.files[0])
    {
        // update_crops_labels(elem);  // get features of all db images from backend
        
        var formdata=new FormData();
        var faces=document.querySelectorAll(".person>.faces>img");
        var faces_features={};


        var face_labels=document.querySelectorAll(".person");
    
        for (var i=0;i<face_labels.length;i++)
        {
            var faces=face_labels[i].querySelectorAll(".faces>img");
            var face_features=[]
            if (faces.length>0)
            {
                for(var j=0;j<faces.length;j++)
                {
                    face_features.push(faces[j].dataset.features)
                }
                // name:[features_array]
                faces_features[face_labels[i].querySelector("input").value]=face_features;
                
            }
        }
        formdata.append("db_images",JSON.stringify(faces_features));
        formdata.append("image",elem.files[0]);
        
        console.log(formdata.get("db_images"));
        if(formdata.get("db_images")=="{}"){
            console.log("Add db_images_first")
            return ;
        }
        // console.log(elem.files[0]);
        var loader_txt=show_loading_bar();
        const myInterval=start_timer(loader_txt,0.2);

        fetch("/demo/face_recognition/",{
            method:"POST",
            body:formdata
        }).then(function(response){
            return response.json();
        }).then(function(response){
            console.log(response);
            document.querySelector("#face_rec_image").src="data:image/jpeg;base64,"+response['image'];
            
            clearInterval(myInterval);
            hide_loading_bar();
        })
        
        
    }
}


function remove_person(person){
    var unassigned_faces=document.querySelector("#unassigned_faces");
    var all_crops=person.querySelectorAll(".faces>img");
    all_crops.forEach(function(crop){
        unassigned_faces.appendChild(crop);
    })
    person.remove();
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

function start_timer(el,interval){
    //interval in seconds
    el.innerText="";
    
    var time=0;
    return setInterval(function () { 
        time+=interval;
        el.innerText=time.toFixed(2)+"s";
    }, interval*1000);
}

function show_loading_bar(){
    loader.classList.remove("hidden");
    return loader.querySelector("#loader_text");
}

function hide_loading_bar(){
    loader.classList.add("hidden");
}