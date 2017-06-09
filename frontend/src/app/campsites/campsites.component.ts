import { Component, OnInit } from "@angular/core";
import { ActivatedRoute } from "@angular/router";
import { CampSite, FreePark } from "../models";
import { SearchService } from "../services";
import { CampSitesFilterComponent } from "../campsites-filter";

@Component({
    selector: 'free-sites',
    providers: [CampSitesFilterComponent],
    styleUrls: ['./campsites.component.css'],
    templateUrl: './campsites.component.html'
})
export class CampSitesComponent implements OnInit {
    public park: FreePark = null;
    // Contains campsites to display
    public freeSites: CampSite[] = [];
    // Contains all campsites that are free for the current park
    private allSites: CampSite[] = [];
    // Park name is populated from the route params
    private _parkName: string = '';
    // Contains mapping of filter key to the quality or privacy values that
    // should be displayed (by being in freeSites).
    private readonly filterMap = {
        Poor: ['Poor', 'Average', 'Good'],
        Average: ['Average', 'Good'],
        Good: ['Good']
    };

    constructor(private searchService: SearchService,
                private route: ActivatedRoute) {}

    public ngOnInit() {
        this.route.params.subscribe(
            // Once the park name is available from the route params then
            // set it. See the parkName setter for what happens next.
            (params) => this.parkName = params['parkName']
        );
    }

    set parkName(parkName: string) {
        this._parkName = parkName;
        // Search for free campsites in the park
        this.searchService.searchFreeSites(parkName)
            .subscribe(
                (results) => {
                    if (results) {
                        this.freeSites = results.sites;
                        this.allSites = results.sites;
                        let parkInfo = results.park;
                        parkInfo.freeSites = results.sites.length;
                        this.park = parkInfo;
                    }
                    return results;
                },
                (error) => {
                    throw error;
                }
            );
    }

    get parkName() {
        return this._parkName;
    }

    public filter(event) {
        // Filter freeSites to only contain campsites that have the
        // desired privacy and quality values.
        let showPrivacy = this.filterMap[event.privacy];
        let showQuality = this.filterMap[event.quality];

        this.freeSites = this.allSites.filter(
            (campsite) => {
                return (
                    showPrivacy.indexOf(campsite.details['Privacy:']) > -1 &&
                    showQuality.indexOf(campsite.details['Quality:']) > -1
                );
            }
        );
    }
}
