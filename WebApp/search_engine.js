document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.getElementById('search-btn')

    let oldSearchInput = ""

    searchButton.addEventListener('click', () => {
        const newSearchInput = document.getElementById('search-input').value

        console.log(newSearchInput)

        if (newSearchInput && newSearchInput.length != 0 && newSearchInput != oldSearchInput) {
            query(newSearchInput)
            oldSearchInput = newSearchInput
        }
    })
})


function query(newSearchInput) {
    fetch('http://127.0.0.1:2000/retrieve-relevant-documents', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newSearchInput)
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    }).then(data => {
        console.log('Response from server:', data);
        clearForList()
        if (data.relevant_documents.length > 0) {
            createList(data.relevant_documents)
        }
        else {
            displayNoResults()
        }

    }).catch(error => {
        console.error('There was a problem with the fetch operation:', error);
        // Handle errors
    });
}

function clearForList() {
    let imageContainerToRemove = document.getElementById("inactive-image-container");
    if (imageContainerToRemove) {
        imageContainerToRemove.remove()
    }

    let listContainerToRemove = document.getElementById("list-container");
    if (listContainerToRemove) {
        listContainerToRemove.remove()
    }

    let noResultsMessageContainerToRemove = document.getElementById("no-results-message-container")
    if (noResultsMessageContainerToRemove) {
        noResultsMessageContainerToRemove.remove()
    }
}

function displayNoResults() {
    let container = document.getElementById("container")

    const noResultsMessageContainer = document.createElement("div")
    noResultsMessageContainer.classList.add("no-results-message-container")
    noResultsMessageContainer.id = "no-results-message-container"

    const noResultsMessage = document.createElement("div")
    noResultsMessage.classList.add("no-results-message")
    noResultsMessage.textContent = "No Results"

    noResultsMessageContainer.appendChild(noResultsMessage)

    container.appendChild(noResultsMessageContainer)
}


function createList(relevantDocuments) {
    let container = document.getElementById("container")

    const listContainer = document.createElement("div");
    listContainer.classList.add("list-container");
    listContainer.id = "list-container"


    for (const relevantDocument of relevantDocuments) {
        //list item 
        let listItem = document.createElement("div");
        listItem.classList.add("list-item");
        listContainer.appendChild(listItem)

        //image of faculty member
        let facultyMemberImage = document.createElement("img");
        facultyMemberImage.classList.add("faculty-member-image");
        facultyMemberImage.src = relevantDocument[1][2]
        console.log(facultyMemberImage)
        listItem.appendChild(facultyMemberImage)

        //div container for other info
        let facultyInfoDiv = document.createElement("div")
        facultyInfoDiv.classList.add("faculty-info-container")
        listItem.appendChild(facultyInfoDiv)

        //name of faculty member
        let facultyMemberName = document.createElement("div")
        facultyMemberName.classList.add("info-text-name")
        facultyMemberName.textContent = relevantDocument[1][0]
        facultyInfoDiv.appendChild(facultyMemberName)

        //degree and focus of faculty member
        if (relevantDocument[1][1]) {
            let facultyMemberDegreeAndFocus = document.createElement("div")
            facultyMemberDegreeAndFocus.classList.add("info-text")
            facultyMemberDegreeAndFocus.textContent = relevantDocument[1][1]
            facultyInfoDiv.appendChild(facultyMemberDegreeAndFocus)
        }

        //phone number of faculty member 
        if (relevantDocument[1][3]) {
            let facultyMemberPhoneNumber = document.createElement("div")
            facultyMemberPhoneNumber.classList.add("info-text")
            facultyMemberPhoneNumber.textContent = relevantDocument[1][3]
            facultyInfoDiv.appendChild(facultyMemberPhoneNumber)
        }

        //office location of faculty member
        if (relevantDocument[1][4]) {
            let facultyMemberOfficeLocation = document.createElement("div")
            facultyMemberOfficeLocation.classList.add("info-text")
            facultyMemberOfficeLocation.textContent = relevantDocument[1][4]
            facultyInfoDiv.appendChild(facultyMemberOfficeLocation)
        }

        //office location of faculty member
        if (relevantDocument[1][5]) {
            let facultyMemberEmailAddress = document.createElement("div")
            facultyMemberEmailAddress.classList.add("info-text")
            facultyMemberEmailAddress.textContent = relevantDocument[1][5]
            facultyInfoDiv.appendChild(facultyMemberEmailAddress)
        }

        //link of faculty member webpage
        let link = document.createElement("a");
        link.href = relevantDocument[0]
        link.textContent = relevantDocument[0]
        link.target = "_blank"
        facultyInfoDiv.appendChild(link)
    }

    container.appendChild(listContainer)
}