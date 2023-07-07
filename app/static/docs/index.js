var base_url=window.location.href.split("/").slice(0,3).join("/");
// console.log(base_url);


var data={
    "route_name":"get_crops",
    "route":"/api/get_crops",
    "method":"POST",
    "summary":"This route is used to get face crops from any image",
    "request_params":[
        {"name":"image","summary":"Image to get face crops from.","type":"File","required":"*"},
        {"name":"access_key","summary":"access key related with your account.","type":"json","required":"*"},
        {"name":"settings-parameter","summary":"pass any settings for example \"d_thres\":0.3 .","type":"json","required":""},
    ],
    "response_params":[
        {"name":"message","summary":"\"success\" if everything is fine.","type":"Text"},
        {"name":"crops","summary":"return list of crop images.","type":"list of base64 values"},
    ],
}



function add_endpoint(data){
    // <div class="endpoint">
    //             <h3 class="route_name">get_crops</h3> 
    //             <h4>Method:<span class="method_type">POST</span></h4>
    //             <p class="summary">This route is used to get face crops from any image</p>
    //             <p><b>route:&#9;</b><span class="api_route">/api/get_crops</span></p>
                
                
    //             <b>Request Parameters:</b>
    //             <ul>
    //                 <li>
    //                     <span><span class="param_name">image<span>:&#9;</span>
    //                     <span class="param_summary">Image to get face crops from.</span>
    //                     <span>(Type:&#9;<span class="param_type">File</span>)</span>
    //                 </li>
    //                 <li>
    //                     <span><span class="param_name">settings-parameter<span>:&#9;</span>
    //                     <span class="param_summary">pass any settings for example "d_thres":0.3 .</span>
    //                     <span>(Type:&#9;<span class="param_type">json</span>)</span>
    //                 </li>
    //                 <li>
    //                     <span><span class="param_name">access_key<span>:&#9;</span>
    //                     <span class="param_summary">access key related with your account.</span>
    //                     <span>(Type:&#9;<span class="param_type">json</span>)</span>
    //                 </li>
                    
    //             </ul>
    //             <b>Response Body:</b>
    //             <ul>
    //                 <li>
                        
    //                     <span><span class="param_name">message<span>:&#9;</span>
    //                     <span class="param_summary">"success" if everything is fine.</span>
    //                     <span>(Type:&#9;<span class="param_type">Text</span>)</span>
    //                 </li>
    //                 <li>
                        
    //                     <span><span class="param_name">crops<span>:&#9;</span>
    //                     <span class="param_summary">return list of crop images.</span>
    //                     <span>(Type:&#9;<span class="param_type">list of base64 values</span>)</span>
    //                 </li>
                    
    //             </ul>
                
                
    //         </div>
    var parent_div=document.querySelector(".container");
    var endpoint=document.createElement("div");
    endpoint.className="endpoint";
    // console.log(("color" in data));
    if ("color" in data) {
        endpoint.style.backgroundColor=data["color"];
    }
    parent_div.appendChild(endpoint);
    
    endpoint.innerHTML+=`<h3 class="route_name">${data['route_name']}</h3> `;
    endpoint.innerHTML+=`<h4>Method:&#9;<span class="method_type">${data['method']}</span></h4>`;
    endpoint.innerHTML+=`<p class="summary">${data['summary']}</p>`;
    endpoint.innerHTML+=`<p><b>route:&#9;</b><span class="api_route">${base_url+data["route"]}</span></p>`;
    endpoint.innerHTML+=`<b>Request Parameters:</b>`;
    
    var params=document.createElement("ul");
    endpoint.appendChild(params);

    data['request_params'].map(param=>{
        // request parameters

        var list=document.createElement("li");
        list.innerHTML+=`<span><span class="param_name">${param["name"]}<span>:&#9;</span>`;
        list.innerHTML+=`<span class="param_summary">${param['summary']}</span>`;
        list.innerHTML+=`<span>(Type:&#9;<span class="param_type">${param['type']}</span>)${param['required']}</span>`;
        params.appendChild(list);

    })
    endpoint.innerHTML+=`<b>Response Body:</b>`;
    var params=document.createElement("ul");
    endpoint.appendChild(params);
    data['response_params'].map(param=>{
        // response parameters
        
        var list=document.createElement("li");
        list.innerHTML+=`<span><span class="param_name">${param['name']}<span>:&#9;</span>`;
        list.innerHTML+=`<span class="param_summary">${param["summary"]}</span>`;
        list.innerHTML+=`<span>(Type:&#9;<span class="param_type">${param["type"]}</span>)</span>`;
        params.appendChild(list);

    })
    
}




fetch("json/").then(res=>{return res.json();}).then(res=>{
res.map(data=>{
    add_endpoint(data);
})
})



