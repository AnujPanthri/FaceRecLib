// demo2 page start

const label=document.querySelector("#label");

const addBtn=document.querySelector("#add-img");



addBtn.addEventListener("click",()=>{
        const card=document.createElement('div')
        card.classList.add("card")
        card.innerHTML=` <img src="../static/media/hero1.jpg" alt="">
        <button type="submit" id="add-label" class="color-btn">Add label here</button>`

        label.appendChild(card)
})

const addLabel=document.querySelector("#add-label");

const labelBtn=document.querySelector("#label-btn")
const labelInput=document.querySelector("#label-input")


labelBtn.addEventListener("click",()=>{
        labelBtn.classList.add("active")
        labelInput.classList.remove("active")
})



labelInput.addEventListener("focusout",(e)=>{ 
        labelBtn.classList.remove("active")
        labelInput.classList.add("active")
        labelBtn.innerText=labelInput.value;
        if(labelInput.value==""){
                labelBtn.innerText="Add Label Here"
        }
})

labelInput.addEventListener("keydown",(e)=>{ 
       
        if(e.key =='Enter' || e.keyCode==13){
                labelBtn.classList.remove("active")
        labelInput.classList.add("active")
        labelBtn.innerText=labelInput.value;
        }
        if(labelInput.value==""){
                labelBtn.innerText="Add Label Here"
        }
})
        






// const bar=document.querySelector("#bar");
// const xbar=document.querySelector("#xbar")

// const navLink=document.querySelector("#header .nav-link");




// bar.addEventListener("click",()=>{
//         navLink.classList.add("active")
//         bar.classList.add("active")
//         xbar.classList.add("active")
        
// })

// xbar.addEventListener("click",()=>{
//     navLink.classList.remove("active")
//         bar.classList.remove("active")
//         xbar.classList.remove("active")
// })


