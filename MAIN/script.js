// {x:"px" ,y:"px", width:"px",height:"px",content:"",custom_style:"",custom_onclick:""},

var block1 = [
            {x: "320px", y: "0px", width:"480px", height:"160px", content:"<p>Welcome to my launcher !</p><p>its still in pre alpha tho</p><p>but its finally functional !</p>",custom_style:"display: initial;padding-top: 20px;"},
            {x: "0px",y:"480px", width:"160px",height:"160px",content:"",custom_style:"background-image: url(../images/image3ds.png); background-size:contain;",custom_onclick:"window.location='../systems/index.html';"},
            {x:"320px" ,y:"320px", width:"480px",height:"320px",content:"<video controls width=\"460px\" style=\"border-radius: 20px;\"><source src=\"../videos/trailer.mp4\" type=\"video/mp4\"></video>",custom_style:"",custom_onclick:""},
            {x:"0px" ,y:"640px", width:"160px",height:"160px",content:"Click above to see a game selection exemple page",custom_style:"text-align: center;",custom_onclick:""},

            {x:"800px" ,y:"160px", width:"160px",height:"160px",content:"Click on the notepad block to launch the windows notepad ! (requires local server running)",custom_style:"text-align: center;",custom_onclick:""},
            {x:"960px", y:"160px", width:"160px", height:"160px", content:"<p>Notepad</p>", custom_style:"text-align: center;color: rgb(83, 0, 63);", custom_onclick:"launchLocalApp('notepad').catch(error => document.getElementById('launcher-status').textContent = error.message);"},
        ]




function create_blocks(b_list) {
    const container = document.querySelector(".container");
    container.replaceChildren();
    b_list.forEach(block => {
        let newblock = document.createElement("div");
        newblock.classList.add("draggable");
        newblock.style.left = block.x;
        newblock.style.top = block.y;
        newblock.style.width = block.width;
        newblock.style.height = block.height;
        newblock.innerHTML = block.content;
        if (block.custom_style) {
            newblock.style.cssText += block.custom_style;
        }
        newblock.blockData = block;
        newblock.classList.toggle("has-click-action", Boolean(block.custom_onclick && block.custom_onclick.trim()));
        newblock.onclick = function() {
            if (!isEditingMode && block.custom_onclick) {
                eval(block.custom_onclick);
            }
        };
        container.appendChild(newblock);
        newblock.addEventListener('mousedown', startDrag);
        if (isEditingMode) {
            addBlockSettingsButton(newblock);
        }
    });
}



function single_block(block) {
            console.log("creating single block")
                let newblock = document.createElement("div");
                newblock.classList.add("draggable");
                newblock.style.left = block.x;
                newblock.style.top = block.y;
                newblock.style.width = block.width;
                newblock.style.height = block.height;
                newblock.innerHTML = block.content;
                if (block.custom_style) {
                    newblock.style.cssText += block.custom_style;
                }
                newblock.onclick = function() {
                    if (block.custom_onclick) {
                        eval(block.custom_onclick);
                    }
                };
                document.querySelector(".container").appendChild(newblock);
                newblock.addEventListener('mousedown', startDrag);
                block1.push(block);
                newblock.blockData = block;
                newblock.classList.toggle("has-click-action", Boolean(block.custom_onclick && block.custom_onclick.trim()));
                saveBlock1();
    }


function getBlock1Cookie() {
    const cookie = document.cookie
        .split(";")
        .map(value => value.trim())
        .find(value => value.startsWith("block1="));
    return cookie ? decodeURIComponent(cookie.slice("block1=".length)) : null;
}

function saveBlock1() {
    const serializedBlocks = JSON.stringify(block1);
    const encodedBlocks = encodeURIComponent(serializedBlocks);
    let cookieFailure = "Cookies are unavailable.";

    try {
        if (encodedBlocks.length <= 3800) {
            document.cookie = `block1=${encodedBlocks}; max-age=31536000; path=/; SameSite=Lax`;
            if (getBlock1Cookie() === serializedBlocks) {
                try {
                    localStorage.removeItem("block1");
                } catch (error) {
                    console.warn("Could not clear the local storage fallback:", error);
                }
                return true;
            }
        } else {
            cookieFailure = "The cookie storage limit was exceeded.";
        }
    } catch (error) {
        console.warn("Could not save blocks in cookies:", error);
    }

    try {
        localStorage.setItem("block1", serializedBlocks);
        if (localStorage.getItem("block1") === serializedBlocks) {
            const status = document.getElementById("launcher-status");
            if (status) {
                status.textContent = `Blocks saved in local browser storage because ${cookieFailure.toLowerCase()}`;
            }
            return true;
        }
    } catch (error) {
        console.error("Could not save blocks in local browser storage:", error);
    }

    const status = document.getElementById("launcher-status");
    if (status) {
        status.textContent = `Blocks could not be saved. ${cookieFailure} Local browser storage is also unavailable.`;
    }
    return false;
}

function loadBlock1() {
    try {
        let savedBlocks = null;
        try {
            savedBlocks = localStorage.getItem("block1");
        } catch (error) {
            console.warn("Local browser storage is unavailable; trying cookies instead.", error);
        }
        if (savedBlocks === null) {
            savedBlocks = getBlock1Cookie();
        }
        if (savedBlocks === null) {
            return false;
        }
        const parsedBlocks = JSON.parse(savedBlocks);
        if (!Array.isArray(parsedBlocks)) {
            throw new Error("Saved blocks are not a list.");
        }
        block1 = parsedBlocks;
        return true;
    } catch (error) {
        const status = document.getElementById("launcher-status");
        if (status) {
            status.textContent = "Saved blocks could not be loaded. The default blocks will be shown.";
        }
        console.error("Could not load saved blocks:", error);
        return false;
    }
}

loadBlock1();
create_blocks(block1)