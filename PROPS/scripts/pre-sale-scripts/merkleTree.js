const { MerkleTree } = require('merkletreejs')
const keccak256 = require('keccak256');
var fs = require("fs");

function main() {

    const runIndex = fs.readdirSync('out/').length + 1;
    const currFileName = "out/MerkleTree.json"
    const runTstamp = Date.now();
    const addyList = fs.readFileSync("./markletree_INPUT", "utf-8").replace(/(\r)/gm, "");
    const leaves_array = addyList.split("\n")
    const leaves = leaves_array.map(x => keccak256(x))
    const tree = new MerkleTree(leaves, keccak256, { sortPairs: true })
    const root = tree.getRoot().toString('hex')

    var full_json = '{ "root": "' + root + '", "addys":[';

    leaves_array.forEach(function (item, index) {
        full_json = full_json + '"' + item + '"'
        if (index != leaves_array.length - 1) {
            full_json = full_json + ", "
        }
    });
    full_json = full_json + '], ';

    full_json = full_json + '"proofs":[';
    leaves_array.forEach(function (item, index) {
        hexProof = tree.getHexProof(keccak256(item))
        full_json = full_json + '"' + hexProof.toString() + '"'
        if (index != leaves_array.length - 1) {
            full_json = full_json + ","
        }
    });
    full_json = full_json + ']}';
    var full_json_obj = JSON.parse(full_json)
    var full_json_pretty = JSON.stringify(full_json_obj, null, 2);
    file_name = "out/" + runIndex + "_MerkleTree_" + runTstamp + ".json";
    try {
        fs.writeFileSync(file_name, full_json_pretty)
        //file written successfully
        console.log("Merkle tree written to file " + file_name)
    } catch (err) {
        console.error(err)
    }

    if (fs.existsSync(currFileName)) {
        console.log("Deleting file " + currFileName);
        fs.unlinkSync(currFileName);
    }
    fs.copyFile(file_name, currFileName, (err) => {
        if (err) throw err;
        return
    });

    return
}

main()



/*
//if (!fs.existsSync(dir)) {
//    console.log("Creating dir " + dir);
//   fs.mkdirSync(dir);
//}
file_name = dir + "/MerkleTree.out";
try {
    fs.writeFileSync(file_name, tree.toString())
    //file written successfully
    console.log("Merkle tree written to file " + file_name)
} catch (err) {
    console.error(err)
}

file_content_full = "List of addys: \n" + text + "\n\n\n Merkle Tree: \n" + tree.toString() + "\n\n\n Root: " + root;
file_name_full = dir + "/MerkleTree_full.out";
try {
    fs.writeFileSync(file_name_full, file_content_full)
    //file written successfully
    console.log("Merkle tree FULL written to file " + file_name_full)
} catch (err) {
    console.error(err)
}



file_name_proof = dir + "/MerkleTree_proofs.out";
try {
    fs.writeFileSync(file_name_proof, proofs)
    //file written successfully
    console.log("Merkle tree PROOFS written to file " + file_name_full)
} catch (err) {
    console.error(err)
}

file_name_proof = dir + "/MerkleTree_root.out";
try {
    fs.writeFileSync(file_name_proof, root)
    //file written successfully
    console.log("Merkle tree PROOFS written to file " + file_name_full)
} catch (err) {
    console.error(err)
}
return*/