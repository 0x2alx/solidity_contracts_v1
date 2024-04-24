const basePath = process.cwd();
const { MODE } = require(`${basePath}/constants/blend_mode.js`);
const { NETWORK } = require(`${basePath}/constants/network.js`);

const network = NETWORK.eth;

// General metadata for Ethereum
const namePrefix = "Crazy Sassy Exes";
const description = "Crazy Sassy Exes is a PFP project. However, all traits are hand drawn and carefully colored by Marleen (Studio Irida). As you might know, Marleen loves colors and paying attention to details. The goal is to make every PFP look like a little 1/1 piece. Art is always the main utility.";
const baseUri = "https://ghooost0x2a.xyz/cse/imgs";

const solanaMetadata = {
  symbol: "YC",
  seller_fee_basis_points: 1000, // Define how much % you want from secondary market sales 1000 = 10%
  external_url: "https://www.youtube.com/c/hashlipsnft",
  creators: [
    {
      address: "7fXNuer5sbZtaTEPhtJ5g5gNtuyRoKkvxdjEjEnPN4mC",
      share: 100,
    },
  ],
};

// If you have selected Solana then the collection starts from 0 automatically
const layerConfigurations = [
  {
    growEditionSizeTo: 5,
    layersOrder: [
      { name: "Background", options: { bypassDNA: true } },
      { name: "Skin" },
      { name: "Mouth" },
      { name: "Eyes" },
      { name: "Hair" },
      { name: "Face Tatt" },
      { name: "Body Tatt" },
      { name: "Clothes" },
      { name: "Earrings" },
      { name: "Hair Piece" },
    ],
  },
  {
    growEditionSizeTo: 7,
    layersOrder: [
      { name: "Background", options: { bypassDNA: true } },
      { name: "Skin" },
      { name: "Mouth" },
      { name: "Eyes" },
      { name: "Hair" },
      { name: "Face Tatt" },
      { name: "Body Tatt" },
      { name: "Clothes" },
      { name: "Earrings" },
    ],
  },
  {
    growEditionSizeTo: 9,
    layersOrder: [
      { name: "Background", options: { bypassDNA: true } },
      { name: "Skin" },
      { name: "Mouth" },
      { name: "Eyes" },
      { name: "Hair" },
      { name: "Face Tatt" },
      { name: "Body Tatt" },
      { name: "Clothes" },
    ],
  },
];

const shuffleLayerConfigurations = true;

const debugLogs = false;

const format = {
  width: 2000,
  height: 2000,
  smoothing: false,
};

const gif = {
  export: false,
  repeat: 0,
  quality: 100,
  delay: 500,
};

const text = {
  only: false,
  color: "#ffffff",
  size: 20,
  xGap: 40,
  yGap: 40,
  align: "left",
  baseline: "top",
  weight: "regular",
  family: "Courier",
  spacer: " => ",
};

const pixelFormat = {
  ratio: 2 / 128,
};

const background = {
  generate: true,
  brightness: "80%",
  static: false,
  default: "#000000",
};

const extraMetadata = {
  external_url: "https://twitter.com/CrazySassyExes"
};

const rarityDelimiter = "#";

const uniqueDnaTorrance = 10000;

const preview = {
  thumbPerRow: 5,
  thumbWidth: 50,
  imageRatio: format.height / format.width,
  imageName: "preview.png",
};

const preview_gif = {
  numberOfImages: 5,
  order: "ASC", // ASC, DESC, MIXED
  repeat: 0,
  quality: 100,
  delay: 500,
  imageName: "preview.gif",
};

module.exports = {
  format,
  baseUri,
  description,
  background,
  uniqueDnaTorrance,
  layerConfigurations,
  rarityDelimiter,
  preview,
  shuffleLayerConfigurations,
  debugLogs,
  extraMetadata,
  pixelFormat,
  text,
  namePrefix,
  network,
  solanaMetadata,
  gif,
  preview_gif,
};
